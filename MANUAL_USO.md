# Manual de Uso y Pruebas

Este documento describe cómo instalar, ejecutar y probar el laboratorio web vulnerable a Inyección SQL, y cómo validar la mitigación con consultas parametrizadas.

> **Advertencia ética:** las pruebas se realizan únicamente en este laboratorio local, con datos ficticios. Probar estas técnicas contra sistemas de terceros es un delito informático.

## 1. Requisitos previos

- Python 3.10 o superior
- Git
- Visual Studio Code (opcional)

## 2. Instalación

1. Clonar el repositorio y entrar a la carpeta del proyecto:

```bash
git clone https://github.com/KNELAZO/proyecto-sqli-flask.git
cd proyecto-sqli-flask
```

2. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

No es necesario ejecutar ningún script de inicialización de la base de datos: `app_vulnerable.py` crea `usuarios_prueba.db` automáticamente al arrancar, con tres usuarios ficticios.

| Usuario     | Clave                | Correo                    | Rol           |
|-------------|----------------------|---------------------------|---------------|
| admin_demo  | AdminFicticio123     | admin@example.test        | administrador |
| estudiante1 | ClaveFicticia123     | estudiante@example.test   | estudiante    |
| invitado    | InvitadoFicticio123  | invitado@example.test     | invitado      |

> **Nota:** `database/init_db.py` es una versión anterior del proyecto y no lo usa la aplicación actual. No debe ejecutarse para este laboratorio.

## 3. Ejecución del servidor vulnerable

Desde la raíz del proyecto:

```bash
python app_vulnerable.py
```

El servidor queda disponible en **http://127.0.0.1:5000**. Rutas:

| Ruta | Método | Función |
|---|---|---|
| `/` | GET | Página principal |
| `/login` | GET | Formulario de inicio de sesión |
| `/buscar` | GET | Formulario de búsqueda de usuarios |
| `/api/login` | POST | Recibe `username` y `password` y consulta la tabla `usuarios` |
| `/api/search` | GET | Recibe `q` y busca usuarios por nombre |

Para detenerlo, presionar `Ctrl + C` en la terminal.

## 4. Pruebas antes de la mitigación (versión vulnerable)

Las consultas se construyen por concatenación de cadenas:

```python
consulta = (
    "SELECT usuario, rol FROM usuarios "
    f"WHERE usuario = '{usuario}' AND clave = '{clave}'"
)
```

```python
consulta = (
    "SELECT usuario, correo, rol FROM usuarios "
    f"WHERE usuario LIKE '%{termino}%'"
)
```

### 4.1 Pruebas de inicio de sesión (`/api/login`)

Comando de ejemplo:

```bash
curl -X POST http://127.0.0.1:5000/api/login --data-urlencode "username=ENTRADA" --data-urlencode "password=ENTRADA"
```

| # | `username` | `password` | Respuesta del servidor | HTTP | Interpretación |
|---|---|---|---|---|---|
| L1 | `admin_demo` | `AdminFicticio123` | `{"autenticado":true,"rol":"administrador","usuario":"admin_demo"}` | 200 | Comportamiento normal: credenciales válidas. |
| L2 | `admin_demo` | `mal` | `{"autenticado":false,"mensaje":"Usuario o contraseña incorrectos."}` | 401 | Comportamiento normal: clave incorrecta. |
| L3 | `admin_demo' OR '1'='1' -- ` | `clave_incorrecta` | `{"autenticado":true,"rol":"administrador","usuario":"admin_demo"}` | 200 | **Bypass de autenticación.** `OR '1'='1'` hace verdadera la condición y `--` comenta la verificación de la clave. |
| L4 | `admin_demo' -- ` | `x` | `{"autenticado":true,"rol":"administrador","usuario":"admin_demo"}` | 200 | **Bypass dirigido** a una cuenta concreta, sin conocer su clave. |
| L5 | `'` | `x` | `{"mensaje":"Ocurrió un error en la consulta SQL."}` | 400 | **Error de sintaxis.** Confirma que la entrada llega a la consulta sin sanear. |
| L6 | `x' OR (SELECT substr(clave,1,1) FROM usuarios WHERE usuario='admin_demo')='A' -- ` | `x` | `{"autenticado":true,...}` | 200 | **Inyección ciega basada en booleanos.** La respuesta cambia según la condición. Con `='Z'` (L7) la respuesta es 401, así que la clave puede extraerse carácter por carácter. |

### 4.2 Pruebas de búsqueda (`/api/search`)

Comando de ejemplo:

```bash
curl -G http://127.0.0.1:5000/api/search --data-urlencode "q=ENTRADA"
```

| # | `q` | Respuesta del servidor | HTTP | Interpretación |
|---|---|---|---|---|
| S1 | `estudiante` | `{"cantidad":1,"resultados":[{"correo":"estudiante@example.test","rol":"estudiante","usuario":"estudiante1"}]}` | 200 | Comportamiento normal: una coincidencia. |
| S2 | `%' UNION SELECT usuario, clave, rol FROM usuarios -- ` | `"cantidad":6`, con las claves visibles en el campo `correo` | 200 | **UNION SELECT.** La consulta agrega filas de la misma tabla, con las columnas en el orden que el atacante elige. Las claves aparecen en el campo que la API llama `correo`, porque la búsqueda original devuelve tres columnas y la inyectada las pone en esa posición. |
| S3 | `'` | `{"mensaje":"Ocurrió un error en la consulta SQL."}` | 400 | **Error de sintaxis**, igual que L5. |

### 4.3 Prueba con el script de ataque

El script `ataque_sql_i.py` ejecuta dos payloads contra el servidor local (debe estar en ejecución):

```bash
python ataque_sql_i.py
```

Ejecuta el bypass de autenticación (L3) y la búsqueda UNION (S2), y muestra las respuestas en formato JSON. Solo apunta a `127.0.0.1`.

## 5. Validación de la mitigación (consultas parametrizadas)

La mitigación reemplaza la concatenación por consultas con marcadores `?`. Los valores se pasan por separado, así SQLite los trata siempre como datos y nunca como parte de la sentencia:

```python
# Login
consulta = "SELECT usuario, rol FROM usuarios WHERE usuario = ? AND clave = ?"
resultado = conexion.execute(consulta, (usuario, clave)).fetchone()

# Búsqueda
consulta = "SELECT usuario, correo, rol FROM usuarios WHERE usuario LIKE ?"
resultados = conexion.execute(consulta, (f"%{termino}%",)).fetchall()
```

Las pruebas se repitieron sobre una copia de `origin/main` con este cambio, en el puerto 5001 y con la misma base de datos:

| # | Entrada | Versión vulnerable | Versión parametrizada | Resultado |
|---|---|---|---|---|
| L1 | Login legítimo | Acceso concedido | Acceso concedido | Correcto: el uso legítimo sigue funcionando. |
| L3 | `' OR '1'='1' --` | **Acceso concedido** | Acceso denegado (401) | **Neutralizado.** |
| L4 | `admin_demo' --` | **Acceso concedido** | Acceso denegado (401) | **Neutralizado.** |
| L5 | `'` | **Error SQL (400)** | Acceso denegado (401) | **Neutralizado.** El error ya no llega al usuario. |
| L6 | Consulta booleana | **Respuesta distinta según la condición** | Acceso denegado (401) | **Neutralizado.** |
| S1 | `estudiante` | Una coincidencia | Una coincidencia | Correcto. |
| S2 | UNION | **6 filas, incluidas las claves** | 0 filas | **Neutralizado.** |
| S3 | `'` | **Error SQL (400)** | 200 sin resultados | **Neutralizado.** |

### Tabla resumen comparativa

| Prueba | Antes (vulnerable) | Después (parametrizada) |
|---|---|---|
| Login legítimo (L1) | Acceso concedido | Acceso concedido |
| Bypass con `' OR '1'='1' --` (L3) | **Acceso concedido sin clave** | Acceso denegado |
| Bypass con `admin_demo' --` (L4) | **Acceso concedido** | Acceso denegado |
| Error de sintaxis visible (L5, S3) | **Mensaje de error visible** | Sin error visible |
| Extracción booleana (L6) | **Respuesta distinta según la condición** | Sin diferencia |
| UNION SELECT (S2) | **Claves expuestas** | Sin resultados |

> **Estado:** la mitigación se validó en una copia local. Todavía no está integrada en `origin/main`; debe entrar por la rama del Integrante 4. Cuando se integre, hay que repetir las pruebas sobre esa versión.

## 6. Limitaciones del entorno

- `debug=False` en `app_vulnerable.py`, así que no hay depurador expuesto.
- Las claves se guardan en texto plano. Es una mala práctica que el informe debe señalar.
- `database/init_db.py` está desactualizado y no lo usa la aplicación.
