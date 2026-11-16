# English Quiz – Android (versión inicial)

Aplicación de práctica de inglés con Python, Kivy y SQLite.

## Funciones incluidas
- Secciones Reading, Listening, Speaking, Writing y Conversations.
- Temas iniciales de nivel A1.
- Ejercicios con respuesta escrita y retroalimentación básica.
- Base de datos SQLite local.
- Pantalla para agregar nuevos temas por categoría.
- Botón de reproducción para ejercicios de Listening.

## Probar en Windows
1. Instala Python 3.11.
2. Abre una terminal dentro de esta carpeta.
3. Ejecuta: `py -3.11 -m venv venv`
4. Activa el entorno: `venv\\Scripts\\activate`
5. Instala Kivy: `pip install -r requirements.txt`
6. Ejecuta: `python main.py`

## Crear APK Android
La compilación Android con Buildozer se realiza desde Linux. En Windows puedes usar WSL2 con Ubuntu.
Sigue la instalación oficial: https://buildozer.readthedocs.io/
Desde Ubuntu, dentro de la carpeta del proyecto, ejecuta: `buildozer android debug`
El APK se genera en la carpeta `bin/`.

## Audios
Copia archivos MP3 en `assets/audio/`. El ejercicio de ejemplo de Listening busca `bank.mp3`.

## Alcance de esta primera versión
La navegación, base de datos, ejercicios iniciales y creación de temas están preparados.
Listening requiere archivos MP3. Speaking permite practicar oralmente, pero la grabación y evaluación automática de pronunciación se incorporarán en una siguiente versión. El panel agrega temas; la administración completa de preguntas y audios también puede ampliarse.
