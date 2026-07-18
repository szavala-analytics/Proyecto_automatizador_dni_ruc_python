#!/bin/bash
# Script de arranque rapido para Mac.
# Uso: abrir Terminal, ubicarse en esta carpeta, y ejecutar: ./iniciar.sh

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "Creando entorno virtual..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "Iniciando servidor en http://127.0.0.1:5000"
python3 app.py
