# English Quiz — inglés A1

Aplicación de aprendizaje de inglés hecha con Python, Kivy y SQLite. Funciona en Windows y se puede empaquetar para Android con Buildozer.

## Funciones

- **Práctica guiada:** Reading, Listening, Speaking, Writing y Conversations, con ejercicios e imágenes.
- **Contenido inicial:** lecciones de las unidades 1 a 7 de Top Notch Fundamentals.
- **Evaluación:** examen mixto o por unidad, con 25 preguntas. Si una unidad tiene menos de 25 preguntas, se completa con preguntas aleatorias de otras unidades sin repetir.
- **Audio y voz:** síntesis de voz para practicar; el reconocimiento por micrófono está disponible en Android. En Windows, el botón de voz informa que se debe escribir el mensaje.
- **Chat en línea:** salas de conversación por código mediante Firebase Realtime Database.
- **Cuentas y roles:** registro e inicio de sesión por correo con Firebase Authentication. El registro público siempre crea usuarios normales; el rol de administrador se asigna manualmente en Firebase.
- **Importación de PDF con Gemini:** procesa libros en sesiones de hasta 40 páginas y guarda el avance por lote para poder continuar. También se pueden crear y administrar temas manualmente.
- **Vistas por rol:** los usuarios normales practican, hacen quizzes y conversan; no ven Manage/PDF ni botones de borrado. El administrador conserva la pantalla de administración actual.
- **Biblioteca compartida:** el administrador publica automáticamente en Firebase los ejercicios importados y los temas/ejercicios manuales; las reimportaciones, ediciones y eliminaciones reemplazan el contenido compartido. Los usuarios lo descargan al iniciar sesión y mientras la app está abierta en Inicio.
- **Imágenes compartidas:** en la publicación normal, los recortes de los ejercicios se suben a un bucket público de Supabase Storage. En el ejercicio, el alumno puede ampliarlos. El PDF original no se publica.
- **Importación solo texto:** el administrador puede marcar **Solo texto (sin imágenes)**. Tras confirmar, la biblioteca compartida se publica en Firebase sin imágenes. Esto no borra las imágenes existentes en Supabase.
- **Progreso por cuenta:** los intentos y estadísticas se sincronizan en Firebase por usuario. El contenido inicial sigue siendo local en cada dispositivo.

## Archivos principales

- `main.py`: interfaz Kivy, pantallas, lógica de práctica y examen, SQLite, voz y configuración.
- `book_units.py` y `units_data.py`: contenido de las unidades precargadas.
- `pdf_importer.py`: procesamiento de PDF e integración con Gemini.
- `online_chat.py`: cliente REST de Firebase para el chat.
- `firebase_client.py`: autenticación, progreso y biblioteca compartida mediante Firebase REST.
- `supabase_storage.py`: publicación y descarga de imágenes con Supabase Storage.
- `firebase_database.rules.json` y `supabase_storage_policies.sql`: reglas de seguridad para Firebase Realtime Database y Supabase Storage.
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
3. La importación procesa hasta 40 páginas por sesión y guarda el avance después de cada lote. Deja **Solo texto (sin imágenes)** desmarcado para publicar imágenes con Supabase, o márcalo para publicar sin imágenes.
4. Pulsa **Seleccionar libro PDF e Importar**. Si el libro tiene más de 40 páginas, vuelve a elegir exactamente el mismo PDF para continuar desde la siguiente página guardada. Si quieres corregir los recortes de un PDF ya importado, marca **Reanalizar desde el inicio**; reemplazará los ejercicios de ese PDF y pedirá confirmación.
5. Elige el archivo en el selector. La importación requiere conexión a Internet.

La app guarda la clave localmente en SQLite cuando se inicia la importación y la vuelve a cargar después. **No agregues la clave de Gemini al código, al README ni a Git.** Si una clave se expone, revócala y genera otra. En ambos modos se envían a Gemini las páginas del PDF para analizarlas; en solo texto no se generan recortes ni se publican imágenes. En Android el PDF se procesa con `PdfRenderer`; en Windows se usa PyMuPDF.

El avance se guarda cada dos páginas analizadas. Si la app se cierra o falla la conexión, selecciona el mismo archivo PDF para continuar desde la última página guardada. Mantén la misma opción de imágenes durante toda la importación.

## Cuentas, roles y reglas de Firebase

La app usa el proyecto de Firebase configurado por `FIREBASE_DB_URL` en `main.py`. Antes de iniciar sesión:

1. En Firebase Console, habilita **Authentication → Sign-in method → Email/Password**.
2. Copia la **Web API Key** de **Project settings → General** y configúrala en `FIREBASE_WEB_API_KEY` en `main.py`. La API key identifica el proyecto; no sustituye las reglas de seguridad.
3. En **Realtime Database → Rules**, publica el contenido de `firebase_database.rules.json`. Las salas quedan disponibles para usuarios autenticados, el progreso es privado por UID y solo un administrador puede publicar la biblioteca.
4. Crea la cuenta del administrador desde **Authentication → Users** y copia su UID. La app reconoce el custom claim `admin: true`; también admite el valor de texto `"admin"` en `/roles/<UID>` para conservar la configuración anterior. Las reglas impiden que la app o un usuario registrado cambien roles.
5. Crea un proyecto de Supabase y un bucket **público** para las imágenes (por ejemplo, `exercise-images`). En **Authentication → Third-Party Auth**, conecta el proyecto de Firebase usando su Project ID.
6. Asigna los custom claims `admin: true` y `role: authenticated` al UID administrador desde un entorno confiable con Firebase Admin SDK. La app usa `admin` para mostrar las opciones de administración y Supabase usa estos claims para autorizar las cargas. El valor legado `/roles/<UID> = "admin"` por sí solo no autoriza cargas en Supabase. Por ejemplo:

   ```python
   import firebase_admin
   from firebase_admin import auth, credentials

   firebase_admin.initialize_app(
       credentials.Certificate("service-account.json")
   )
   auth.set_custom_user_claims(
       "UID_DEL_ADMIN", {"admin": True, "role": "authenticated"}
   )
   ```

   Instala `firebase-admin` solo en ese entorno administrativo. No incluyas el archivo de cuenta de servicio en la app ni en Git. Después de asignar los claims, el administrador debe cerrar e iniciar sesión otra vez para recibir un token actualizado.
7. En Supabase, abre el SQL Editor, sustituye `YOUR_BUCKET_NAME` y `YOUR_FIREBASE_PROJECT_ID` en `supabase_storage_policies.sql`, y ejecuta el archivo. En **Manage / PDF**, la URL del proyecto, la clave publishable y el bucket están preconfigurados en `main.py`. La clave publishable está diseñada para clientes; nunca incluyas una clave `secret` o `service_role`. Al guardar, la biblioteca se publica usando los claims recién asignados.
8. Los demás usuarios se registran desde la app. El bucket es público para descargar las imágenes compartidas; las políticas solo permiten publicar, reemplazar o borrar imágenes a la cuenta administradora.

El contenido del administrador se guarda en `/shared_content/snapshot` de Realtime Database y sus imágenes en Supabase Storage. La app actualiza la copia local al iniciar sesión y cada minuto mientras el usuario permanece en Inicio. El PDF original nunca se sube. Supabase Free tiene cuotas de almacenamiento y transferencia. El progreso se guarda como eventos identificados por UID; los intentos anteriores a las cuentas permanecen sin asignar. El token de renovación se guarda en el directorio privado de datos de la app; la contraseña no se guarda.

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

- Los ejercicios iniciales, temas y PDF se guardan en `english_quiz.db`, dentro del directorio de datos de Kivy. El progreso por usuario se sincroniza también con Firebase.
- Los temas y ejercicios administrados se publican en Firebase Realtime Database; las imágenes se publican en Supabase Storage para que las cuentas puedan practicarlos. Al ser un bucket público, quien tenga la URL de una imagen puede verla.
- La clave de Gemini se guarda localmente en esa base de datos; no está cifrada por esta aplicación.
- La importación de PDF envía imágenes de las páginas seleccionadas a la API de Gemini. El PDF original no se comparte; solo se publican los ejercicios y sus imágenes recortadas.
- El correo se autentica con Firebase Authentication. El progreso y los mensajes del chat se transmiten a Firebase con el token de sesión.
