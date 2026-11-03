# Manual de Uso y Pruebas

Este documento detalla los pasos para instalar, ejecutar y probar el entorno vulnerable y su respectiva mitigación.

## Requisitos Previos
- Python 3.10 o superior
- Git
- Visual Studio Code (opcional)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/KNELAZO/proyecto-sqli-flask.git
cd proyecto-sqli-flask
pip install -r requirements.txt
python database/init_db.py
python app_vulnerable.py
