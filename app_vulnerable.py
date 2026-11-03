from pathlib import Path
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("usuarios_prueba.db")


def crear_base_datos():
    """Crea una base de datos local con usuarios ficticios."""
    conexion = sqlite3.connect(DB_PATH)

    try:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                clave TEXT NOT NULL,
                correo TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        """)

        cantidad = conexion.execute(
            "SELECT COUNT(*) FROM usuarios"
        ).fetchone()[0]

        if cantidad == 0:
            conexion.executemany(
                """
                INSERT INTO usuarios (usuario, clave, correo, rol)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        "admin_demo",
                        "AdminFicticio123",
                        "admin@example.test",
                        "administrador",
                    ),
                    (
                        "estudiante1",
                        "ClaveFicticia123",
                        "estudiante@example.test",
                        "estudiante",
                    ),
                    (
                        "invitado",
                        "InvitadoFicticio123",
                        "invitado@example.test",
                        "invitado",
                    ),
                ],
            )

        conexion.commit()
    finally:
        conexion.close()


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/login")
def pagina_login():
    return render_template("login.html")


@app.get("/buscar")
def pagina_busqueda():
    return render_template("busqueda.html")


@app.post("/api/login")
def login():
    usuario = request.form.get("username", "")
    clave = request.form.get("password", "")

    # Vulnerable a propósito para la práctica controlada de SQL Injection.
    consulta = (
        "SELECT usuario, rol FROM usuarios "
        f"WHERE usuario = '{usuario}' AND clave = '{clave}'"
    )

    conexion = sqlite3.connect(DB_PATH)

    try:
        resultado = conexion.execute(consulta).fetchone()
    except sqlite3.Error:
        return jsonify({"mensaje": "Ocurrió un error en la consulta SQL."}), 400
    finally:
        conexion.close()

    if resultado:
        return jsonify({
            "autenticado": True,
            "usuario": resultado[0],
            "rol": resultado[1],
        })

    return jsonify({
        "autenticado": False,
        "mensaje": "Usuario o contraseña incorrectos.",
    }), 401


@app.get("/api/search")
def buscar():
    termino = request.args.get("q", "")

    # Vulnerable a propósito: concatena el término dentro de la consulta.
    consulta = (
        "SELECT usuario, correo, rol FROM usuarios "
        f"WHERE usuario LIKE '%{termino}%'"
    )

    conexion = sqlite3.connect(DB_PATH)

    try:
        resultados = conexion.execute(consulta).fetchall()
    except sqlite3.Error:
        return jsonify({"mensaje": "Ocurrió un error en la consulta SQL."}), 400
    finally:
        conexion.close()

    return jsonify({
        "cantidad": len(resultados),
        "resultados": [
            {
                "usuario": fila[0],
                "correo": fila[1],
                "rol": fila[2],
            }
            for fila in resultados
        ],
    })


if __name__ == "__main__":
    crear_base_datos()
    app.run(host="127.0.0.1", port=5000, debug=False)