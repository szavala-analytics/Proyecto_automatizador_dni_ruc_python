"""
Script de linea de comandos para uso automatico (por ejemplo con cron).

Lee el archivo data/entrada/documentos.txt (un documento por linea),
consulta las APIs, actualiza el maestro de clientes y guarda un
respaldo historico con marca de tiempo.

Uso manual:
    python3 main_cli.py

Uso con un archivo distinto:
    python3 main_cli.py /ruta/a/otra_lista.txt
"""

import os
import sys
from dotenv import load_dotenv

from core.procesador import procesar_lista, actualizar_maestro, guardar_historico
from core.drive_uploader import subir_maestro_a_drive

load_dotenv()

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_ENTRADA_DEFECTO = os.path.join(CARPETA_BASE, "data", "entrada", "documentos.txt")
CARPETA_HISTORICO_LOCAL = os.path.join(CARPETA_BASE, "data", "historico")


def main():
    token = os.getenv("DECOLECTA_API_TOKEN", "")
    carpeta_salida = os.getenv("DRIVE_OUTPUT_PATH", "").strip()

    if not token:
        print("ERROR: no se encontro DECOLECTA_API_TOKEN en el archivo .env")
        sys.exit(1)

    ruta_entrada = sys.argv[1] if len(sys.argv) > 1 else ARCHIVO_ENTRADA_DEFECTO

    if not os.path.exists(ruta_entrada):
        print(f"ERROR: no existe el archivo de entrada: {ruta_entrada}")
        print("Crea ese archivo con un numero de documento (DNI u RUC) por linea.")
        sys.exit(1)

    with open(ruta_entrada, "r", encoding="utf-8") as archivo:
        lista_documentos = [linea.strip() for linea in archivo if linea.strip() != ""]

    if not lista_documentos:
        print("El archivo de entrada esta vacio. No hay nada que procesar.")
        sys.exit(0)

    print(f"Procesando {len(lista_documentos)} documento(s)...")
    resultados = procesar_lista(lista_documentos, token)

    if not carpeta_salida:
        carpeta_salida = os.path.join(CARPETA_BASE, "data")

    os.makedirs(carpeta_salida, exist_ok=True)
    ruta_csv_maestro = os.path.join(carpeta_salida, "maestro_clientes.csv")
    ruta_xlsx_maestro = os.path.join(carpeta_salida, "maestro_clientes.xlsx")

    actualizar_maestro(resultados, ruta_csv_maestro, ruta_xlsx_maestro)
    ruta_respaldo = guardar_historico(resultados, CARPETA_HISTORICO_LOCAL)

    print(f"Maestro actualizado en: {ruta_csv_maestro}")
    print(f"Version Excel en:       {ruta_xlsx_maestro}")
    print(f"Respaldo historico en:  {ruta_respaldo}")

    url_apps_script = os.getenv("APPS_SCRIPT_URL", "").strip()
    if url_apps_script:
        try:
            subir_maestro_a_drive(ruta_csv_maestro, ruta_xlsx_maestro)
            print("Maestro subido/actualizado en Google Drive correctamente.")
        except Exception as error:
            print(f"AVISO: no se pudo subir a Google Drive: {error}")

    print("Proceso finalizado correctamente.")


if __name__ == "__main__":
    main()
