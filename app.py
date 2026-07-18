"""
Aplicacion web local (Flask) para automatizar el registro de clientes
individuales (DNI) y corporativos (RUC).

Ejecutar con: python3 app.py
Luego abrir en el navegador: http://127.0.0.1:5000
"""

import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from dotenv import load_dotenv

from core.procesador import procesar_lista, actualizar_maestro, guardar_historico
from core.drive_uploader import subir_maestro_a_drive

load_dotenv()

APP_TOKEN = os.getenv("DECOLECTA_API_TOKEN", "")
CARPETA_SALIDA = os.getenv("DRIVE_OUTPUT_PATH", "").strip()

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_HISTORICO_LOCAL = os.path.join(CARPETA_BASE, "data", "historico")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "clave-local-desarrollo")

ultimo_resultado = {"filas": [], "ruta_csv": None, "ruta_xlsx": None}


def obtener_carpeta_destino():
    """
    Si el usuario configuro DRIVE_OUTPUT_PATH en el .env, el maestro se
    guarda directamente ahi (carpeta sincronizada de Google Drive).
    Si no, se guarda dentro de data/ del propio proyecto.
    """
    if CARPETA_SALIDA:
        return CARPETA_SALIDA
    return os.path.join(CARPETA_BASE, "data")


@app.route("/", methods=["GET"])
def inicio():
    return render_template(
        "index.html",
        token_configurado=bool(APP_TOKEN),
        carpeta_destino=obtener_carpeta_destino(),
        resultado=ultimo_resultado,
    )


@app.route("/procesar", methods=["POST"])
def procesar():
    global ultimo_resultado

    if not APP_TOKEN:
        flash("No se encontro DECOLECTA_API_TOKEN en el archivo .env. Configuralo antes de continuar.")
        return redirect(url_for("inicio"))

    documentos_texto = request.form.get("documentos", "")
    lista_documentos = [linea.strip() for linea in documentos_texto.splitlines() if linea.strip() != ""]

    archivo_subido = request.files.get("archivo")
    if archivo_subido and archivo_subido.filename != "":
        contenido = archivo_subido.read().decode("utf-8", errors="ignore")
        for linea in contenido.splitlines():
            linea_limpia = linea.strip().strip(",")
            if linea_limpia != "":
                lista_documentos.append(linea_limpia)

    if not lista_documentos:
        flash("No se ingreso ningun documento. Pega una lista o sube un archivo.")
        return redirect(url_for("inicio"))

    resultados = procesar_lista(lista_documentos, APP_TOKEN)

    carpeta_destino = obtener_carpeta_destino()
    os.makedirs(carpeta_destino, exist_ok=True)

    ruta_csv_maestro = os.path.join(carpeta_destino, "maestro_clientes.csv")
    ruta_xlsx_maestro = os.path.join(carpeta_destino, "maestro_clientes.xlsx")

    actualizar_maestro(resultados, ruta_csv_maestro, ruta_xlsx_maestro)
    guardar_historico(resultados, CARPETA_HISTORICO_LOCAL)

    ultimo_resultado = {
        "filas": resultados,
        "ruta_csv": ruta_csv_maestro,
        "ruta_xlsx": ruta_xlsx_maestro,
    }

    mensaje_drive = ""
    url_apps_script = os.getenv("APPS_SCRIPT_URL", "").strip()
    if url_apps_script:
        try:
            subir_maestro_a_drive(ruta_csv_maestro, ruta_xlsx_maestro)
            mensaje_drive = " El maestro tambien se subio/actualizo en tu carpeta de Google Drive."
        except Exception as error:
            mensaje_drive = f" AVISO: no se pudo subir a Google Drive ({error})."

    flash(
        f"Proceso terminado. {len(resultados)} documento(s) procesado(s). "
        f"Maestro actualizado en: {carpeta_destino}.{mensaje_drive}"
    )
    return redirect(url_for("inicio"))


@app.route("/descargar/<tipo>")
def descargar(tipo):
    if tipo == "csv" and ultimo_resultado["ruta_csv"]:
        return send_file(ultimo_resultado["ruta_csv"], as_attachment=True)
    if tipo == "xlsx" and ultimo_resultado["ruta_xlsx"]:
        return send_file(ultimo_resultado["ruta_xlsx"], as_attachment=True)
    flash("Todavia no se ha generado ningun archivo.")
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    os.makedirs(os.path.join(CARPETA_BASE, "data"), exist_ok=True)
    os.makedirs(CARPETA_HISTORICO_LOCAL, exist_ok=True)
    app.run(host="127.0.0.1", port=5000, debug=True)
