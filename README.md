# Automatizacion de Clientes y Proveedores (DNI + RUC)

Proyecto que detecta automaticamente si un numero de documento es DNI (8 digitos)
o RUC (11 digitos), consulta el endpoint correspondiente de decolecta.com,
y consolida todo en un maestro unico (CSV y Excel) listo para usarse en Power BI.

---

## 📄 Manual de uso

**[Ver el Manual de uso completo (PDF)](Manual_de_uso_Proyecto_Python.pdf)**

Haz clic en el enlace de arriba para leerlo directamente en el visor de GitHub, sin necesidad de descargarlo.

---

## 1. Requisitos previos

- Mac con Python 3.12 (`python3 --version` -> Python 3.12.10)
- Una cuenta en https://decolecta.com para obtener un token de API
- Una App web en Google Apps Script.
- Power BI en el navegador (app.powerbi.com) con tu cuenta habitual

---

## 2. Obtener el token de la API de decolecta

1. Entra a https://decolecta.com y crea una cuenta.
2. Entra al panel/dashboard de tu cuenta y genera un token de API (API Key).
3. Copia ese token, lo usaras en el paso 4.

Nota: las dos APIs (DNI y RUC) requieren el encabezado
`Authorization: Bearer TU_TOKEN`. Sin token, las llamadas devolveran error 401.

---

## 3. Ubicar el proyecto en tu Mac

1. Descomprime el archivo `clientes-proveedores.zip`.
2. Muevelo a una carpeta fija, por ejemplo:
   ```
   /Users/admin/Proyectos/clientes-proveedores
   ```
3. Abre la Terminal y entra a esa carpeta:
   ```
   cd /Users/admin/Proyectos/clientes-proveedores
   ```

---

## 4. Configurar el entorno

1. Crea el entorno virtual:
   ```
   python3 -m venv venv
   ```
2. Activa el entorno virtual:
   ```
   source venv/bin/activate
   ```
   (veras que el prompt de la Terminal cambia y muestra "(venv)" al inicio)
3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Crea tu archivo de configuracion real a partir del ejemplo:
   ```
   cp .env.example .env
   ```
5. Abre el archivo `.env` con cualquier editor de texto (o con `nano .env`)
   y completa:
   ```
   DECOLECTA_API_TOKEN=el_token_que_copiaste_en_el_paso_2
   APPS_SCRIPT_URL=genera_un_nuevo_proyecto_en_google_Apps_scripts_como_app_web_esa_url_la_pegas_aquí
   FLASK_SECRET_KEY=escribe_cualquier_texto_secreto
   ```
   Guarda el archivo.

---

## 5. Ejecutar el sitio web local

Con el entorno virtual activado, ejecuta:

```
python3 app.py
```

Veras un mensaje similar a:

```
Running on http://127.0.0.1:5000
```

Abre esa direccion en tu navegador (Chrome, Safari, el que uses).
Ahi encontraras:

- Un cuadro de texto para pegar una lista de documentos (uno por linea,
  mezclando DNI y RUC sin problema).
- Un boton para subir un archivo .txt o .csv con documentos, uno por linea.
- Un boton "Procesar documentos".

Al procesar, el sistema:

1. Detecta el tipo de cada documento por su cantidad de digitos.
2. Consulta el endpoint de RENIEC (DNI) o SUNAT (RUC) segun corresponda.
3. Actualiza el archivo maestro (`maestro_clientes.csv` y `maestro_clientes.xlsx`)
   en la carpeta que configuraste en `APPS_SCRIPT_URL`.
4. Guarda ademas una copia con fecha y hora en `data/historico/` (dentro del
   propio proyecto) para fines de auditoria.
5. Muestra en pantalla una tabla con los resultados y botones para descargar
   el CSV o el Excel directamente desde el navegador.

Para apagar el servidor, vuelve a la Terminal y presiona `Ctrl + C`.

La proxima vez que quieras usarlo, solo necesitas:
```
cd /Users/admin/Proyectos/clientes-proveedores
source venv/bin/activate
python3 app.py
```
---

## 6. Automatizar corridas sin abrir el navegador (opcional)

Si quieres que el maestro se actualice solo, por ejemplo todos los dias a
las 8:00 a.m., a partir de una lista fija de documentos:

1. Edita el archivo `data/entrada/documentos.txt` y pon ahi, uno por linea,
   los documentos que quieres consultar en cada corrida automatica.
2. Prueba manualmente que funcione:
   ```
   cd /Users/admin/Proyectos/clientes-proveedores
   source venv/bin/activate
   python3 main_cli.py
   ```
3. Programa la tarea con cron. En la Terminal escribe:
   ```
   crontab -e
   ```
4. Agrega esta linea (ajusta la ruta a la tuya) y guarda:
   ```
   0 8 * * * /Users/admin/Proyectos/clientes-proveedores/venv/bin/python3 /Users/admin/Proyectos/clientes-proveedores/main_cli.py >> /Users/admin/Proyectos/clientes-proveedores/data/historico/log_cron.txt 2>&1
   ```
   Esto ejecuta el script todos los dias a las 8:00 a.m. y guarda un registro
   de lo que ocurrio en `log_cron.txt`.

Nota: cron solo se ejecuta si tu Mac esta encendida en ese horario.

---

## 7. Aspectos en GitHub y "desplegarlo" como sitio web

Puntos importantes que debes tener claros:

- **GitHub Pages** (el hosting gratuito de GitHub) solo sirve paginas
  estaticas (HTML, CSS, JavaScript). No puede ejecutar Python ni Flask.
  Por lo tanto, este proyecto **no puede funcionar como sitio en vivo en
  GitHub Pages**, porque necesita un servidor que ejecute Python y llame a
  las APIs con tu token de forma segura.
- Lo que si puedes hacer en GitHub es **guardar el codigo fuente** como
  respaldo y control de versiones (no la app en vivo, solo el codigo).
- Si de verdad quieres que la aplicacion funcione como sitio web accesible
  desde cualquier lugar (no solo en tu Mac), necesitas un servicio que si
  ejecute Python, como Render.com, Railway.app o PythonAnywhere. Esto es
  opcional y se explica en la seccion 8.2.

### 8.1 Subir el codigo a GitHub (respaldo, no despliegue)

1. Crea una cuenta en https://github.com si no tienes.
2. Crea un repositorio nuevo vacio, por ejemplo `clientes-proveedores`.
3. En la Terminal, dentro de la carpeta del proyecto:
   ```
   git init
   git add .
   git commit -m "Version inicial del proyecto"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/clientes-proveedores.git
   git push -u origin main
   ```
   El archivo `.gitignore` ya esta configurado para que tu archivo `.env`
   (con el token) y los datos generados **nunca** se suban a GitHub.

### 8.2 Desplegarlo como sitio en vivo (opcional)

Si quieres que el formulario web sea accesible desde internet y no solo
desde tu Mac, la opcion mas simple es Render.com (tiene un plan gratuito):

1. Sube el codigo a GitHub (paso 8.1).
2. Entra a https://render.com y crea una cuenta.
3. Crea un "New Web Service" y conectalo a tu repositorio de GitHub.
4. En "Build Command" pon: `pip install -r requirements.txt`
5. En "Start Command" pon: `python app.py`
6. En la seccion de variables de entorno de Render, agrega
   `DECOLECTA_API_TOKEN` con tu token real (no lo pongas en el codigo).
7. En este escenario, `APPS_SCRIPT_URL` no aplica de la misma forma
   porque el servidor ya no es tu Mac; el maestro se guardaria en el
   propio servidor de Render y tendrias que descargarlo desde ahi o
   integrar la API de Google Drive para subirlo automaticamente
   (paso adicional, no incluido en esta primera version).
8. Ten en cuenta que un sitio publico sin clave de acceso puede ser usado
   por cualquiera que encuentre la URL y gastar las consultas de tu token.
   Si despliegas esto en publico, conviene agregarle una contrasena simple.

---

## 9. Usar el maestro de clientes en Power BI (navegador, sin Power BI Desktop)

### Opcion A: Subir el archivo Excel manualmente (la mas simple)

1. Cada vez que proceses documentos, se genera `maestro_clientes.xlsx`
   dentro de tu carpeta de Google Drive (ya sincronizada en tu Mac).
2. Entra a https://app.powerbi.com
3. Ve a tu espacio de trabajo ("Mi espacio de trabajo" o el que uses).
4. Haz clic en "Nuevo" -> "Cargar un archivo" -> "Local File"
   (en espanol puede aparecer como "Cargar" o "Obtener datos" segun la
   version de la interfaz).
5. Selecciona el archivo `maestro_clientes.xlsx` desde la carpeta de Drive
   sincronizada en tu Mac.
6. Power BI creara automaticamente un conjunto de datos (dataset) y podras
   construir tu reporte/dashboard con esas columnas:
   `tipo_documento, numero_documento, categoria,
   nombre_completo_razon_social, estado, condicion_situacion, direccion,
   distrito, provincia, departamento, fecha_consulta, observaciones`
7. Cuando proceses documentos nuevos y quieras actualizar el dashboard,
   repites el paso 4-5 (subir de nuevo el archivo) o usas la opcion B para
   automatizar la actualizacion.

### Opcion B: Actualizacion automatica desde Google Drive (mas avanzada)

Si quieres que Power BI se actualice solo, sin que tengas que volver a
subir el archivo cada vez:

1. En Google Drive (navegador), haz clic derecho sobre `maestro_clientes.xlsx`
   -> "Compartir" -> cambia el acceso a "Cualquier persona con el enlace"
   (ten en cuenta que esto hace el archivo accesible a quien tenga el
   enlace, evaluar si es aceptable para informacion de tus clientes).
2. Copia el ID del archivo desde la URL para armar un enlace de descarga
   directa con este formato:
   ```
   https://drive.google.com/uc?export=download&id=ID_DEL_ARCHIVO
   ```
3. En Power BI Service, ve a "Obtener datos" -> "Web" y pega ese enlace.
4. En el panel del conjunto de datos, entra a "Configuracion" ->
   "Actualizacion programada" y activa la actualizacion automatica
   (diaria, cada hora, etc). Ten en cuenta que la actualizacion programada
   con la frecuencia mas alta suele requerir una licencia Power BI Pro
   (Microsoft ofrece una prueba gratuita de 60 dias); revisa tu plan actual
   en la configuracion de tu cuenta de Power BI.

---

## 10. Estructura del proyecto

```
clientes-proveedores/
  app.py                  Aplicacion web (interfaz local en el navegador)
  main_cli.py             Version por linea de comandos (para cron)
  requirements.txt        Dependencias de Python
  .env.example            Plantilla de configuracion
  .gitignore              Evita subir datos y credenciales a GitHub
  core/
    api_client.py          Llamadas a las APIs de decolecta.com
    procesador.py           Deteccion DNI/RUC y consolidacion del maestro
  templates/
    index.html              Interfaz web
  static/
    style.css               Estilos de la interfaz
  data/
    entrada/documentos.txt   Lista de documentos para el modo automatico
    historico/               Respaldos con fecha y hora de cada corrida
 Manual_de_uso_Proyecto_Python.pdf   Manual de uso completo
```

---

## 11. Preguntas frecuentes

**¿Puedo mezclar DNI y RUC en la misma lista?**
Si. El sistema detecta el tipo por la cantidad de digitos (8 = DNI,
11 = RUC) automaticamente, documento por documento.

**¿Que pasa si un documento no existe o esta mal escrito?**
Se registra en el maestro con la columna `observaciones` indicando el
motivo (por ejemplo "DNI no encontrado o invalido (400)"), y no interrumpe
el resto del proceso.

**¿El maestro se sobreescribe cada vez?**
No. Si un documento ya existia, se actualiza con la informacion mas
reciente. Si es nuevo, se agrega. El respaldo historico en
`data/historico/` si guarda una copia nueva por cada corrida.

**¿Necesito Power BI Pro?**
No, para subir el Excel manualmente (Opcion A de la seccion 9) no hace
falta. Solo seria necesario si buscas actualizacion automatica programada
con alta frecuencia (Opcion B).
