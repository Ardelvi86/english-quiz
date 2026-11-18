# English Quiz – Android (Top Notch Fundamentals • Nivel A1)

Aplicación móvil de aprendizaje y práctica de inglés desarrollada con **Python**, **Kivy** y **SQLite**, con soporte de voz nativa en Android, importación automática de libros PDF con Inteligencia Artificial y chat en tiempo real mediante **Firebase Realtime Database**.

---

## Funciones incluidas
- **Práctica Guiada por Áreas:** Secciones de *Reading*, *Listening*, *Speaking*, *Writing* y *Conversations* con soporte de imágenes y ejemplos.
- **Contenido Nivel A1 precargado:** Lecciones y ejercicios estructurados de las **Unidades 1 a 7** (*Top Notch Fundamentals*) listos para usar sin conexión.
- **Evaluación (Quiz) sin pistas:** Exámenes de 10 preguntas aleatorias por unidad o mixtos, con calificación final y desglose de aciertos y errores.
- **Audio y Voz Nativa:** Síntesis de voz (*Text-to-Speech* en velocidad normal y lenta) para *Listening* y *Speaking* (con soporte opcional para archivos MP3 locales en `assets/audio/`).
- **Conversación Online en Tiempo Real:** Salas privadas por código de invitación (ej. `JUAN-24`) conectadas a Firebase Realtime Database, con guías de diálogo del libro y dictado por micrófono nativo de Android (*SpeechRecognizer*).
- **Importador Automático de PDF con IA:** Selección de libros PDF desde el dispositivo para extraer lecciones, recortar ilustraciones (`Pillow`) y generar ejercicios automáticamente mediante la API de **Gemini**, además de gestión manual de temas y ejercicios.
- **Estadísticas y Progreso Local:** Almacenamiento persistente en **SQLite** con métricas de rendimiento por área.

---

## Estructura del proyecto
- `main.py`: Interfaz gráfica (KV), pantallas principales, motor de voz/micrófono nativo y gestión de base de datos SQLite.
- `book_units.py` / `units_data.py`: Contenido precargado de las Unidades 1 a 7.
- `pdf_importer.py`: Procesamiento de archivos PDF, recorte de imágenes y generación de ejercicios con Gemini.
- `online_chat.py`: Cliente REST ligero para sincronización de salas de chat en tiempo real con Firebase.
- `buildozer.spec`: Configuración de empaquetado y permisos para Android.

---

## Configuración previa (Opcional)
- **Chat Online (Firebase):** Configura una instancia de *Firebase Realtime Database* con reglas de lectura/escritura en `/rooms/$room_id` y pega tu URL en `FIREBASE_DB_URL` dentro de `main.py` (o ingrésala desde el panel *Manage / PDF* en la app).
- **Importador PDF (Gemini):** Ingresa tu *Gemini API Key* directamente en la pantalla *Manage / PDF* de la aplicación (se guarda localmente en el dispositivo).

---

## Probar en Windows (PC)
1. Instala **Python 3.11**.
2. Abre una terminal (PowerShell) dentro de la carpeta del proyecto.
3. Crea el entorno virtual:
   ```powershell
   py -3.11 -m venv .venv