"""Importador automático de libros PDF con IA para English Quiz.

Usa android.graphics.pdf.PdfRenderer en Android (cero dependencias C++ pesadas)
y Gemini 3.5 Flash-Lite para extraer unidades, recortar imágenes y crear ejercicios.
"""
import base64
import hashlib
import io
import itertools
import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
import uuid

from kivy.utils import platform
from PIL import Image

from network_utils import create_ssl_context

PROMPT_EXTRACCION = """
Analiza estas páginas de un libro de inglés como material para crear una
actividad de observación y transcripción. Identifica las unidades y sus temas,
y crea preguntas que hagan que el estudiante observe la imagen/actividad del
libro y escriba la respuesta exactamente como aparece allí. Devuelve ÚNICAMENTE JSON válido:
{
  "topics": [
    {
      "category": "Reading | Listening | Speaking | Writing | Conversations",
      "name": "Unit X - Título corto",
      "description": "Breve explicación o regla gramatical",
      "exercises": [
        {
          "prompt": "Pregunta o instrucción clara",
          "passage": "Texto de lectura, audio o ejemplo",
          "answer": "respuesta1|respuesta2",
          "mode": "exact",
          "page_index": 0,
          "image_box": [ymin, xmin, ymax, xmax],
          "image_reason": "qué elemento visual concreto necesita ver el alumno"
        }
      ]
    }
  ]
}
Reglas obligatorias:
- Usa el título/número de unidad y el vocabulario, gramática o función comunicativa
  que se ve en estas páginas. No inventes unidades, temas ni contenido externo.
- El objetivo para el PDF completo es producir entre 20 y 25 ejercicios en total.
  Para este lote crea aproximadamente {batch_target} ejercicios, según el contenido
  disponible. No repitas una pregunta para alcanzar la cantidad.
- Si el objetivo de este lote es 0, identifica el tema/unidad visible y devuelve
  "exercises": [] para reservar las preguntas para otros lotes del mismo libro.
- Prioriza ejercicios e imágenes didácticas del libro: ilustraciones con etiquetas,
  diálogos, tarjetas, mapas, tablas, escenas, instrucciones y actividades. La pregunta
  debe indicar con claridad qué parte observar y qué texto/respuesta escribir.
- Cuando haya texto que el estudiante deba escribir, copia la respuesta del libro
  literalmente: mismas palabras, orden, ortografía y puntuación. No la traduzcas,
  corrijas ni parafrasees. Si hay varias respuestas aceptadas que aparecen en el
  material, sepáralas con | en answer. No inventes una respuesta que no sea legible.
- Cada ejercicio debe poder resolverse mirando la página o el recorte asociado.
  Evita preguntas genéricas, duplicadas o sobre detalles menores.
- Si una página inicia una unidad, conserva su nombre y no mezcles contenidos
  de unidades diferentes. Si no se puede identificar una unidad, usa el título
  visible de la lección o una descripción breve y específica.
- Crea solo ejercicios útiles para practicar el contenido identificado. No
  rellenes categorías que no están respaldadas por estas páginas.
- Asocia una imagen siempre que el ejercicio dependa de una actividad o elemento
  visual de la página. El recorte debe incluir la información necesaria para
  responder (incluido el texto impreso relevante cuando sea parte de la actividad).
  Incluye la actividad completa, sus instrucciones, etiquetas y opciones; deja
  un margen visible alrededor y no ajustes el recorte al borde del contenido.
  No asocies fotos decorativas ni recortes que no permitan contestar.
- Usa "image_box": null y "image_reason": "" únicamente si la pregunta se basa
  en texto corrido y no existe una actividad visual relevante en esas páginas.
- No recortes encabezados, números de página, adornos, fotos decorativas ni la
  página completa. Las coordenadas deben encerrar solo el elemento necesario,
  normalizadas de 0 a 1000 como [ymin, xmin, ymax, xmax].
- "page_index" es el índice (0, 1, ...) de la imagen enviada en este lote.
- Responde en inglés para los ejercicios de práctica de inglés; los nombres de
  unidad pueden conservar el idioma del libro.
"""

PROMPT_EXTRACCION_SOLO_TEXTO = PROMPT_EXTRACCION + (
    "\n- En modo solo texto, no propongas imágenes y usa siempre "
    '"image_box": null.\n'
)

class BookImporter:
    def __init__(self, db, images_dir):
        self.db = db
        self.images_dir = images_dir
        os.makedirs(self.images_dir, exist_ok=True)

    def import_pdf_async(self, pdf_path, api_key,
                         on_progress=None, on_done=None, on_error=None,
                         include_images=True, restart=False):
        thread = threading.Thread(
            target=self._run,
            args=(
                pdf_path, api_key, on_progress, on_done, on_error,
                include_images, restart,
            ),
            daemon=True,
        )
        thread.start()

    def _iter_page_batches(self, pdf_path, batch_size=2, start_page=0):
        """Renderiza páginas por lotes sin cargar el libro entero en RAM."""
        if platform == "android":
            yield from self._iter_android_batches(pdf_path, batch_size, start_page)
        else:
            yield from self._iter_desktop_batches(pdf_path, batch_size, start_page)

    def _iter_android_batches(self, pdf_path, batch_size, start_page=0):
        from jnius import autoclass  # type: ignore[reportMissingImports]

        ParcelFileDescriptor = autoclass("android.os.ParcelFileDescriptor")
        PdfRenderer = autoclass("android.graphics.pdf.PdfRenderer")
        Bitmap = autoclass("android.graphics.Bitmap")
        BitmapConfig = autoclass("android.graphics.Bitmap$Config")
        Canvas = autoclass("android.graphics.Canvas")
        CompressFormat = autoclass("android.graphics.Bitmap$CompressFormat")
        ByteArrayOutputStream = autoclass("java.io.ByteArrayOutputStream")
        File = autoclass("java.io.File")

        java_file = File(pdf_path)
        pfd = ParcelFileDescriptor.open(java_file, ParcelFileDescriptor.MODE_READ_ONLY)
        renderer = PdfRenderer(pfd)

        total = renderer.getPageCount()
        try:
            for start in range(start_page, total, batch_size):
                images = []
                for i in range(start, min(start + batch_size, total)):
                    page = renderer.openPage(i)
                    # Resolución moderada para legibilidad y uso acotado de RAM.
                    w = int(page.getWidth() * 1.5)
                    h = int(page.getHeight() * 1.5)
                    bmp = Bitmap.createBitmap(w, h, BitmapConfig.ARGB_8888)
                    Canvas(bmp).drawRGB(255, 255, 255)
                    page.render(bmp, None, None, 1)
                    page.close()
                    stream = ByteArrayOutputStream()
                    bmp.compress(CompressFormat.JPEG, 85, stream)
                    raw_bytes = bytes(stream.toByteArray())
                    bmp.recycle()
                    images.append(Image.open(io.BytesIO(raw_bytes)))
                yield total, start, images
        finally:
            renderer.close()
            pfd.close()

    def _iter_desktop_batches(self, pdf_path, batch_size, start_page=0):
        try:
            import pymupdf
            doc = pymupdf.open(pdf_path)
            total = len(doc)
            try:
                for start in range(start_page, total, batch_size):
                    images = []
                    for i in range(start, min(start + batch_size, total)):
                        pix = doc[i].get_pixmap(dpi=130)
                        images.append(Image.open(io.BytesIO(pix.tobytes("jpeg"))))
                    yield total, start, images
            finally:
                doc.close()
        except ImportError:
            raise RuntimeError("En PC instala pymupdf (`pip install pymupdf`) para probar PDFs.")

    def _run(self, pdf_path, api_key, on_progress, on_done, on_error,
             include_images=True, restart=False):
        if not api_key:
            if on_error:
                on_error("Pega tu API Key de Gemini antes de importar.")
            return
        staged_images = []
        try:
            source_hash = self._hash_pdf(pdf_path)
            session = self.db.get_pdf_import_session(source_hash)
            if restart:
                old_images = self.db.reset_pdf_import(source_hash)
                for filename in old_images:
                    old_path = os.path.join(self.images_dir, filename)
                    if os.path.isfile(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
                session = None
            if session and bool(session["include_images"]) != bool(include_images):
                raise RuntimeError(
                    "Este libro tiene una importación pendiente con otra opción "
                    "de imágenes. Continúa con la misma opción que usaste al comenzar."
                )
            if session and session["completed"]:
                total = session["total_pages"]
                if on_done:
                    on_done(0, 0, total, total, total, True)
                return

            start_page = session["next_page"] if session else 0
            import_id = uuid.uuid4().hex[:12]
            if on_progress:
                on_progress("Preparando la importación desde la página %d..." % (start_page + 1))
            batch_size = 2
            batch_iterator = iter(self._iter_page_batches(
                pdf_path, batch_size, start_page
            ))
            first_batch = next(batch_iterator, None)
            if first_batch is None:
                if session:
                    total = session["total_pages"]
                    if on_done:
                        on_done(0, 0, total, total, total, True)
                elif on_error:
                    on_error("El PDF no contiene páginas legibles.")
                return
            first_total, _, _ = first_batch
            batches = itertools.chain((first_batch,), batch_iterator)
            session_end = min(start_page + 40, first_total)
            session_topics = 0
            session_exercises = 0
            end_page = start_page
            for total_pages, start, batch_imgs in batches:
                end = min(start + len(batch_imgs), total_pages)
                if start >= session_end:
                    break
                batch_target = (
                    round(end * 22 / total_pages)
                    - round(start * 22 / total_pages)
                )
                if on_progress:
                    on_progress(
                        f"Sesión: páginas {start_page + 1}-{session_end} de "
                        f"{total_pages}. Analizando {start + 1}-{end}..."
                    )

                extraction_prompt = (
                    PROMPT_EXTRACCION
                    if include_images else PROMPT_EXTRACCION_SOLO_TEXTO
                )
                prompt = extraction_prompt.replace(
                    "{batch_target}", str(batch_target)
                )
                parts = [{"text": prompt}]
                for pil_img in batch_imgs:
                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG", quality=80)
                    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})

                data = self._call_gemini(
                    parts, api_key,
                    on_retry=(
                        lambda delay: on_progress(
                            "Gemini está temporalmente saturado. "
                            f"Reintentando páginas {start + 1}-{end} en {delay} s..."
                        ) if on_progress else None
                    ),
                )
                batch_topics = self._prepare_topics(
                    data, batch_imgs, start, source_hash, import_id,
                    staged_images, include_images=include_images,
                )
                created_topics, created_exercises = self.db.save_pdf_import_batch(
                    source_hash,
                    total_pages,
                    end,
                    include_images,
                    batch_topics,
                )
                session_topics += created_topics
                session_exercises += created_exercises
                end_page = end
                staged_images.clear()
                if end_page >= session_end:
                    break

            complete = end_page >= first_total
            if on_done:
                on_done(
                    session_topics,
                    session_exercises,
                    start_page,
                    end_page,
                    first_total,
                    complete,
                )
        except Exception as exc:
            cleanup_errors = []
            for filename in staged_images:
                path = os.path.join(self.images_dir, filename)
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError as cleanup_error:
                    cleanup_errors.append(str(cleanup_error))
            cleanup_message = (
                " No se pudieron limpiar algunas imágenes temporales: "
                + "; ".join(cleanup_errors)
                if cleanup_errors else ""
            )
            if on_error:
                on_error(f"Error al importar: {exc}{cleanup_message}")
            return

    def _call_gemini(self, parts, api_key, on_retry=None):
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3.5-flash-lite:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        attempt = 0
        while True:
            try:
                with urllib.request.urlopen(
                    req, timeout=90, context=create_ssl_context()
                ) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 503):
                    raise
                if exc.code == 429 and attempt >= 5:
                    raise RuntimeError(
                        "Gemini sigue limitando las solicitudes (HTTP 429) "
                        "después de varios reintentos. Espera unos minutos y "
                        "vuelve a importar el PDF."
                    ) from exc
                retry_after = exc.headers.get("Retry-After")
                try:
                    delay = (
                        min(300, max(1, int(retry_after)))
                        if retry_after else min(60, 10 * (2 ** min(attempt, 3)))
                    )
                except (TypeError, ValueError):
                    delay = min(60, 10 * (2 ** min(attempt, 3)))
                if on_retry:
                    on_retry(delay)
                time.sleep(delay)
                attempt += 1
            except urllib.error.URLError as exc:
                reason = exc.reason
                if isinstance(reason, socket.gaierror):
                    raise RuntimeError(
                        "No se pudo encontrar el servidor de Gemini "
                        "(generativelanguage.googleapis.com). Revisa que el "
                        "teléfono tenga internet y que DNS, VPN o DNS privado "
                        "no estén bloqueando la conexión."
                    ) from exc
                raise RuntimeError(
                    "No se pudo conectar con Gemini: %s" % reason
                ) from exc
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)

    @staticmethod
    def _hash_pdf(pdf_path):
        digest = hashlib.sha256()
        with open(pdf_path, "rb") as pdf_file:
            for chunk in iter(lambda: pdf_file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _prepare_topics(self, data, page_images, page_offset, source_hash, import_id,
                        staged_images, include_images=True):
        topics = []
        valid_cats = {"Reading", "Listening", "Speaking", "Writing", "Conversations"}

        for topic_idx, topic in enumerate(data.get("topics", [])):
            cat = topic.get("category", "Reading")
            if cat not in valid_cats:
                cat = "Reading"
            name = (topic.get("name") or "").strip()
            if not name:
                continue

            exercises = []
            for idx, ex in enumerate(topic.get("exercises", [])):
                prompt = (ex.get("prompt") or "").strip()
                answer = (ex.get("answer") or "").strip()
                if not prompt or not answer:
                    continue

                img_filename = ""
                box = ex.get("image_box")
                p_idx = ex.get("page_index", 0)
                image_reason = (ex.get("image_reason") or "").strip()
                if (include_images and image_reason and isinstance(box, list)
                        and len(box) == 4
                        and all(isinstance(value, (int, float)) for value in box)
                        and 0 <= box[0] < box[2] <= 1000
                        and 0 <= box[1] < box[3] <= 1000
                        and isinstance(p_idx, int)
                        and 0 <= p_idx < len(page_images)):
                    img_filename = self._crop_and_save(
                        page_images[p_idx],
                        box,
                        f"book_{source_hash[:12]}_{import_id}_"
                        f"p{page_offset + p_idx}_t{topic_idx}_e{idx}.jpg",
                    )
                    if img_filename:
                        staged_images.append(img_filename)
                exercises.append(
                    {
                        "prompt": prompt,
                        "passage": ex.get("passage", ""),
                        "answer": answer,
                        "mode": ex.get("mode", "exact"),
                        "image_file": img_filename,
                        "full_image_file": "",
                    }
                )

            topics.append(
                {
                    "category": cat,
                    "name": name,
                    "description": topic.get("description", ""),
                    "exercises": exercises,
                }
            )

        return topics

    def _crop_and_save(self, pil_img, box, filename):
        w, h = pil_img.size
        ymin, xmin, ymax, xmax = box
        left = max(0, int((xmin / 1000.0) * w))
        top = max(0, int((ymin / 1000.0) * h))
        right = min(w, int((xmax / 1000.0) * w))
        bottom = min(h, int((ymax / 1000.0) * h))
        pad_x = max(int(w * 0.025), int((right - left) * 0.12))
        pad_y = max(int(h * 0.025), int((bottom - top) * 0.12))
        left = max(0, left - pad_x)
        top = max(0, top - pad_y)
        right = min(w, right + pad_x)
        bottom = min(h, bottom + pad_y)
        if right - left < 20 or bottom - top < 20:
            return ""
        cropped = pil_img.crop((left, top, right, bottom))
        out_path = os.path.join(self.images_dir, filename)
        cropped.save(out_path, format="JPEG", quality=88)
        return filename
