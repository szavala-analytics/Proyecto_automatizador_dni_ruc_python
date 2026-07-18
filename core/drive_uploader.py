"""
Sube (o actualiza) el maestro de clientes directamente en tu carpeta de
Google Drive, usando un Google Apps Script publicado como Web App.

No requiere Google Drive para escritorio ni Google Cloud Console ni
credentials.json: solo necesitas la URL de tu Web App de Apps Script,
configurada en el archivo .env como APPS_SCRIPT_URL.

El ID de la carpeta de destino queda configurado dentro del propio script
de Apps Script (variable ID_CARPETA en script.google.com), no aqui.
"""

import os
import base64
import requests

APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL", "").strip()


def _subir_archivo(ruta_local, nombre_archivo):
    if not APPS_SCRIPT_URL:
        raise Exception("No se configuro APPS_SCRIPT_URL en el archivo .env")

    with open(ruta_local, "rb") as archivo:
        contenido_b64 = base64.b64encode(archivo.read()).decode("utf-8")

    payload = {
        "nombreArchivo": nombre_archivo,
        "contenidoBase64": contenido_b64,
    }

    respuesta = requests.post(APPS_SCRIPT_URL, json=payload, timeout=60)
    respuesta.raise_for_status()
    resultado = respuesta.json()

    if not resultado.get("ok"):
        raise Exception(resultado.get("error", "Error desconocido en Apps Script"))


def subir_maestro_a_drive(ruta_csv, ruta_xlsx, id_carpeta=None):
    """
    Sube (o actualiza si ya existen) el CSV y el XLSX del maestro en la
    carpeta de Drive configurada dentro del script de Apps Script.

    El parametro id_carpeta se mantiene por compatibilidad con las
    llamadas ya existentes en app.py y main_cli.py, pero ya no se usa:
    el ID de carpeta esta hardcodeado en el script de Apps Script.
    """
    if not APPS_SCRIPT_URL:
        return "sin_configurar"

    _subir_archivo(ruta_csv, "maestro_clientes.csv")
    _subir_archivo(ruta_xlsx, "maestro_clientes.xlsx")
    return "ok"
