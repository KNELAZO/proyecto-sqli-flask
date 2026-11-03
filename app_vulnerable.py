from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

# Plantilla HTML básica para el formulario de login
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Login Vulnerable</title></head>
<body>
    <h2>Iniciar Sesión (Vulnerable)</h2>
    <form method="POST" action="/login">
        <label>Usuario:</label><br>
        <input type="text" name="usuario"><br><br>
        <label>Contraseña:</label><br>
        <input type="password" name="clave"><br><br>
        <button type="submit">Ingresar</button>
    </form>
    <p style="color:red;">{{ mensaje }}</p>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, mensaje="")

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form.get('usuario', '')
    clave = request.form.get('clave', '')
    
    # Conexión a la base de datos SQLite
    conn = sqlite3.connect('database/usuarios.db')
    cursor = conn.cursor()

    #  VULNERABILIDAD INTENCIONAL: Concatenación insegura de cadenas
    query = f"SELECT * FROM usuarios WHERE usuario = '{usuario}' AND clave = '{clave}'"
    
    try:
        cursor.execute(query)
        user = cursor.fetchone()
        
        if user:
            return f"<h1>Bienvenido, {usuario}</h1><p>Has iniciado sesión exitosamente.</p>"
        else:
            return render_template_string(HTML_TEMPLATE, mensaje="Credenciales incorrectas")
            
    except Exception as e:
        return f"<h1>Error en la consulta:</h1><p>{str(e)}</p>"
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
