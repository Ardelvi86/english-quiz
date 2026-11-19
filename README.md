# English Quiz — inglés A1

Aplicación de aprendizaje de inglés hecha con Python, Kivy y SQLite. Funciona en Windows y se puede empaquetar para Android con Buildozer.

## Funciones

- **Práctica guiada:** Reading, Listening, Speaking, Writing y Conversations, con ejercicios e imágenes.
- **Contenido inicial:** lecciones de las unidades 1 a 7 de Top Notch Fundamentals.
- **Evaluación:** examen mixto o por unidad, con 25 preguntas. Si una unidad tiene menos de 25 preguntas, se completa con preguntas aleatorias de otras unidades sin repetir.
- **Audio y voz:** síntesis de voz para practicar; el reconocimiento por micrófono está disponible en Android. En Windows, el botón de voz informa que se debe escribir el mensaje.
- **Chat en línea:** salas de conversación por código mediante Firebase Realtime Database.
- **Importación de PDF con Gemini:** selecciona un PDF, elige el máximo de páginas (10 por defecto) y genera temas y ejercicios. También se pueden crear y administrar temas manualmente.
- **Progreso local:** los ejercicios, respuestas y estadísticas se guardan en una base SQLite dentro del directorio de datos de la app.

## Archivos principales

- `main.py`: interfaz Kivy, pantallas, lógica de práctica y examen, SQLite, voz y configuración.
- `book_units.py` y `units_data.py`: contenido de las unidades precargadas.
- `pdf_importer.py`: procesamiento de PDF e integración con Gemini.
- `online_chat.py`: cliente REST de Firebase para el chat.
- `requirements.txt`: dependencias para ejecutar en Windows.
- `buildozer.spec`: dependencias, permisos y configuración de la versión Android.

## Ejecutar en Windows

Se ha probado con Python 3.12 y Kivy 2.3.1.

Desde PowerShell, en la carpeta del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

`requirements.txt` incluye Pillow para imágenes y PyMuPDF para renderizar PDF en Windows. El selector de archivos de Windows permite elegir el PDF directamente.

## Importar un PDF con Gemini

1. Crea una API key en [Google AI Studio](https://aistudio.google.com/app/apikey).
2. En la app, abre **Manage & Importar PDF** y pega la clave en **Gemini API Key**.
3. Indica el máximo de páginas y pulsa **Seleccionar libro PDF e Importar**.
4. Elige el archivo en el selector. La importación requiere conexión a Internet.

La app guarda la clave localmente en SQLite cuando se inicia la importación y la vuelve a cargar después. **No agregues la clave al código, al README ni a Git.** Si una clave se expone, revócala y genera otra. En Android el PDF se procesa con `PdfRenderer`; en Windows se usa PyMuPDF.

Si vuelves a importar exactamente el mismo archivo PDF, se reemplazan sus ejercicios importados anteriores. El contenido precargado, los ejercicios agregados manualmente y los de otros PDF se conservan. Si el procesamiento falla o no genera ejercicios, la importación anterior no se modifica.

## Chat con Firebase

La URL predeterminada está en `FIREBASE_DB_URL` en `main.py`; también se puede cambiar desde **Manage & Importar PDF**. El cliente usa Firebase Realtime Database por REST, en la ruta `/rooms/<código-de-sala>.json`.

El cliente actual no implementa autenticación de Firebase. Configura las reglas de acceso de la base de datos de acuerdo con tu entorno y protege el acceso antes de usarla públicamente; no habilites lectura y escritura abiertas para toda la base en producción.

## Crear una versión Android

La configuración del proyecto está en `buildozer.spec` (Android API 35, mínimo API 24, arquitecturas ARM64 y ARMv7). Buildozer debe ejecutarse en Linux o WSL, no desde PowerShell nativo.

Con Buildozer instalado en Linux/WSL, desde la raíz del proyecto:

```bash
buildozer android debug
```

El APK de depuración se genera en `bin/`. La configuración Android incluye `INTERNET`, `RECORD_AUDIO` y `READ_EXTERNAL_STORAGE`; Android también usa `pyjnius` para las funciones nativas de voz y el selector/renderizador de PDF.

### Compilar con Google Colab

El proyecto incluye `build_android_colab.ipynb`. Se puede abrir directamente desde Google Colab después de subirlo a GitHub:

1. Abre https://colab.research.google.com/
2. Selecciona **Archivo → Subir cuaderno**.
3. Sube `build_android_colab.ipynb`.
4. En el notebook, ejecuta las celdas en orden.
5. Descarga el APK desde la última celda o desde el explorador de archivos de Colab.

Google Colab usa una máquina Linux temporal. Si el código tiene cambios locales que aún no están en GitHub, haz primero:

```powershell
git add .
git commit -m "Preparar compilacion Android"
git push
```

## Datos y privacidad

- Los ejercicios iniciales y el progreso se guardan localmente en `english_quiz.db`, dentro del directorio de datos de Kivy.
- La clave de Gemini se guarda localmente en esa base de datos; no está cifrada por esta aplicación.
- La importación de PDF envía imágenes de las páginas seleccionadas a la API de Gemini.
- El chat envía mensajes y códigos de sala a Firebase.
