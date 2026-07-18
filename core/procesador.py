"""
Logica central del proyecto:
1. Detecta si un numero de documento es DNI (8 digitos) o RUC (11 digitos)
2. Llama al endpoint correspondiente
3. Normaliza ambas respuestas a un esquema unico (maestro de clientes)
4. Guarda el resultado en CSV y XLSX
"""

import os
import time
import csv
import datetime
import pandas as pd

from core.api_client import consultar_dni, consultar_ruc, ESPERA_ENTRE_CONSULTAS

COLUMNAS_MAESTRO = [
    "tipo_documento",
    "numero_documento",
    "categoria",
    "nombre_completo_razon_social",
    "estado",
    "condicion_situacion",
    "direccion",
    "distrito",
    "provincia",
    "departamento",
    "fecha_consulta",
    "observaciones",
]


def limpiar_documento(texto):
    """Elimina espacios, tabulaciones y caracteres no numericos sueltos."""
    return "".join(caracter for caracter in texto.strip() if caracter.isdigit())


def detectar_tipo(numero_documento):
    """
    Devuelve 'DNI', 'RUC' o 'INVALIDO' segun la cantidad de digitos.
    """
    if len(numero_documento) == 8:
        return "DNI"
    if len(numero_documento) == 11:
        return "RUC"
    return "INVALIDO"


def _fila_desde_dni(numero_documento, datos):
    return {
        "tipo_documento": "DNI",
        "numero_documento": numero_documento,
        "categoria": "Persona Natural",
        "nombre_completo_razon_social": datos.get("full_name", ""),
        "estado": "N/A",
        "condicion_situacion": "N/A",
        "direccion": "N/A",
        "distrito": "N/A",
        "provincia": "N/A",
        "departamento": "N/A",
        "fecha_consulta": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observaciones": "Consulta exitosa (RENIEC)",
    }


def _fila_desde_ruc(numero_documento, datos):
    return {
        "tipo_documento": "RUC",
        "numero_documento": numero_documento,
        "categoria": "Persona Juridica",
        "nombre_completo_razon_social": datos.get("razon_social", ""),
        "estado": datos.get("estado", ""),
        "condicion_situacion": datos.get("condicion", ""),
        "direccion": datos.get("direccion", ""),
        "distrito": datos.get("distrito", ""),
        "provincia": datos.get("provincia", ""),
        "departamento": datos.get("departamento", ""),
        "fecha_consulta": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observaciones": "Consulta exitosa (SUNAT)",
    }


def _fila_error(numero_documento, tipo_documento, mensaje):
    return {
        "tipo_documento": tipo_documento,
        "numero_documento": numero_documento,
        "categoria": "N/A",
        "nombre_completo_razon_social": "",
        "estado": "",
        "condicion_situacion": "",
        "direccion": "",
        "distrito": "",
        "provincia": "",
        "departamento": "",
        "fecha_consulta": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "observaciones": mensaje,
    }


def procesar_documento(texto_documento, token):
    """
    Procesa un solo documento (texto crudo) y devuelve un diccionario
    con el esquema COLUMNAS_MAESTRO.
    """
    numero_documento = limpiar_documento(texto_documento)

    if not numero_documento:
        return _fila_error(texto_documento, "INVALIDO", "Documento vacio o sin digitos")

    tipo = detectar_tipo(numero_documento)

    if tipo == "INVALIDO":
        return _fila_error(
            numero_documento,
            "INVALIDO",
            f"Cantidad de digitos no valida ({len(numero_documento)}). Se esperaba 8 (DNI) u 11 (RUC)",
        )

    if tipo == "DNI":
        datos, error = consultar_dni(numero_documento, token)
        if error:
            return _fila_error(numero_documento, "DNI", error)
        return _fila_desde_dni(numero_documento, datos)

    # tipo == "RUC"
    datos, error = consultar_ruc(numero_documento, token)
    if error:
        return _fila_error(numero_documento, "RUC", error)
    return _fila_desde_ruc(numero_documento, datos)


def procesar_lista(lista_documentos, token, progreso_callback=None):
    """
    Procesa una lista de documentos en orden, con una pequena pausa entre
    cada consulta para no saturar la API. Devuelve una lista de diccionarios.
    """
    resultados = []
    total = len(lista_documentos)

    for indice, documento in enumerate(lista_documentos, start=1):
        if documento.strip() == "":
            continue
        fila = procesar_documento(documento, token)
        resultados.append(fila)

        if progreso_callback:
            progreso_callback(indice, total, fila)

        time.sleep(ESPERA_ENTRE_CONSULTAS)

    return resultados


def guardar_historico(resultados, carpeta_historico):
    """
    Guarda una copia con marca de tiempo de esta corrida especifica,
    util para auditoria. No se usa para el dashboard principal.
    """
    os.makedirs(carpeta_historico, exist_ok=True)
    marca_tiempo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_csv = os.path.join(carpeta_historico, f"reporte_{marca_tiempo}.csv")

    dataframe = pd.DataFrame(resultados, columns=COLUMNAS_MAESTRO)
    dataframe.to_csv(ruta_csv, index=False, encoding="utf-8-sig", sep=";")
    return ruta_csv


def actualizar_maestro(resultados, ruta_csv_maestro, ruta_xlsx_maestro):
    """
    Combina los resultados nuevos con el maestro existente.
    Si un numero_documento ya existe, se reemplaza con el dato mas reciente
    (upsert). El maestro final se guarda en CSV y en XLSX en la misma carpeta.
    """
    columnas = COLUMNAS_MAESTRO
    dataframe_nuevo = pd.DataFrame(resultados, columns=columnas)

    if os.path.exists(ruta_csv_maestro):
        dataframe_existente = pd.read_csv(ruta_csv_maestro, dtype=str, encoding="utf-8-sig", sep=";")
    else:
        dataframe_existente = pd.DataFrame(columns=columnas)

    combinado = pd.concat([dataframe_existente, dataframe_nuevo], ignore_index=True)
    combinado["numero_documento"] = combinado["numero_documento"].astype(str)

    # Se queda con la ultima aparicion de cada numero_documento (la mas reciente)
    combinado = combinado.drop_duplicates(subset=["numero_documento"], keep="last")
    combinado = combinado.sort_values(by=["tipo_documento", "numero_documento"]).reset_index(drop=True)

    carpeta_destino = os.path.dirname(ruta_csv_maestro)
    if carpeta_destino:
        os.makedirs(carpeta_destino, exist_ok=True)

    # Se usa punto y coma como separador: con la configuracion regional en
    # espanol (Peru), Excel/Numbers usan la coma como separador decimal, y
    # si el CSV viene separado por comas, todo el contenido se muestra
    # amontonado en la columna A al abrirlo. Con punto y coma, Excel/Numbers
    # reconocen las columnas correctamente de forma automatica.
    combinado.to_csv(ruta_csv_maestro, index=False, encoding="utf-8-sig", sep=";")
    combinado.to_excel(ruta_xlsx_maestro, index=False)

    return combinado
