"""
Cliente HTTP para las APIs de decolecta.com
Contiene las funciones que consultan DNI (RENIEC) y RUC (SUNAT).
"""

import time
import requests

URL_DNI = "https://api.decolecta.com/v1/reniec/dni"
URL_RUC = "https://api.decolecta.com/v1/sunat/ruc/full"

TIMEOUT_SEGUNDOS = 10
REINTENTOS = 2
ESPERA_ENTRE_REINTENTOS = 1.5
ESPERA_ENTRE_CONSULTAS = 0.35  # evita saturar la API


def _encabezados(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def consultar_dni(numero_documento, token):
    """
    Consulta un DNI de 8 digitos en RENIEC.
    Devuelve (datos_dict_o_none, mensaje_error_o_none)
    """
    parametros = {"numero": numero_documento}
    ultimo_error = None

    for intento in range(REINTENTOS + 1):
        try:
            respuesta = requests.get(
                URL_DNI,
                params=parametros,
                headers=_encabezados(token),
                timeout=TIMEOUT_SEGUNDOS,
            )
            if respuesta.status_code == 200:
                return respuesta.json(), None
            if respuesta.status_code == 400:
                return None, "DNI no encontrado o invalido (400)"
            if respuesta.status_code == 401:
                return None, "Token de API invalido o vencido (401)"
            ultimo_error = f"Error HTTP {respuesta.status_code}"
        except requests.exceptions.Timeout:
            ultimo_error = "Tiempo de espera agotado"
        except requests.exceptions.RequestException as error:
            ultimo_error = f"Error de conexion: {error}"

        if intento < REINTENTOS:
            time.sleep(ESPERA_ENTRE_REINTENTOS)

    return None, ultimo_error


def consultar_ruc(numero_documento, token):
    """
    Consulta un RUC de 11 digitos en SUNAT (endpoint full).
    Devuelve (datos_dict_o_none, mensaje_error_o_none)
    """
    parametros = {"numero": numero_documento}
    ultimo_error = None

    for intento in range(REINTENTOS + 1):
        try:
            respuesta = requests.get(
                URL_RUC,
                params=parametros,
                headers=_encabezados(token),
                timeout=TIMEOUT_SEGUNDOS,
            )
            if respuesta.status_code == 200:
                return respuesta.json(), None
            if respuesta.status_code == 400:
                return None, "RUC no encontrado o invalido (400)"
            if respuesta.status_code == 401:
                return None, "Token de API invalido o vencido (401)"
            ultimo_error = f"Error HTTP {respuesta.status_code}"
        except requests.exceptions.Timeout:
            ultimo_error = "Tiempo de espera agotado"
        except requests.exceptions.RequestException as error:
            ultimo_error = f"Error de conexion: {error}"

        if intento < REINTENTOS:
            time.sleep(ESPERA_ENTRE_REINTENTOS)

    return None, ultimo_error
