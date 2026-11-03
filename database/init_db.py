import sqlite3
import os

# Asegurarse de que la carpeta database existe
os.makedirs('database', exist_ok=True)

# Conectar a la base de datos (se creará si no existe)
conn = sqlite3.connect('database/usuarios.db')
cursor = conn.cursor()

# Crear la tabla de usuarios
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    clave TEXT NOT NULL,
    rol TEXT NOT NULL
)
''')

# Insertar usuarios de prueba (borrando los anteriores si existen)
cursor.execute("DELETE FROM usuarios")
usuarios = [
    ('admin', 'admin123', 'administrador'),
    ('profesor', 'profe2026', 'docente'),
    ('estudiante', 'est123', 'alumno')
]
cursor.executemany("INSERT INTO usuarios (usuario, clave, rol) VALUES (?, ?, ?)", usuarios)

conn.commit()
conn.close()

print("Base de datos creada y usuarios insertados correctamente.")
