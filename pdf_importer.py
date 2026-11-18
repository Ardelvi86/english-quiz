"""Importador automático de libros PDF con IA para English Quiz.

Usa android.graphics.pdf.PdfRenderer en Android (cero dependencias C++ pesadas)
y Gemini 2.5 Flash para extraer unidades, recortar imágenes y crear ejercicios.
"""
import base64
import io
import json
import os
import threading
import urllib.request

from kivy.utils import platform
from PIL import Image

PROMPT_EXTRACCION = """
Analiza estas páginas de un libro de inglés y extrae lecciones estructuradas.
Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
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
          "image_box": [ymin, xmin, ymax, xmax]
        }
      ]
    }
  ]
}
Reglas:
- Crea ejercicios variados para Reading, Listening, Speaking, Writing y Conversations según el contenido.
- Si el ejercicio se apoya en una ilustración, diagrama, tarjeta o reloj de la página, incluye "image_box": [ymin, xmin, ymax, xmax] (coordenadas normalizadas 0 a 1000). Si no necesita imagen, pon "image_box": null.
- "page_index" es el índice (0, 1, ...) de la imagen enviada en este lote.
"""


class BookImporter:
    def __init__(self, db, images_dir):
        self.db = db
        self.images_dir = images_dir
        os.makedirs(self.images_dir, exist_ok=True)

    def import_pdf_async(self, pdf_path, api_key, max_pages=10,
                         on_progress=None, on_done=None, on_error=None):
        thread = threading.Thread(
            target=self._run,
            args=(pdf_path, api_key, max_pages, on_progress, on_done, on_error),
            daemon=True,
        )
        thread.start()

    def _render_pages_pil(self, pdf_path, max_pages):
        """Convierte las primeras `max_pages` del PDF a objetos PIL.Image."""
        if platform == "android":
            return self._render_android(pdf_path, max_pages)
        return self._render_desktop(pdf_path, max_pages)

    def _render_android(self, pdf_path, max_pages):
        from jnius import autoclass

        ParcelFileDescriptor = autoclass("android.os.ParcelFileDescriptor")
        PdfRenderer = autoclass("android.graphics.pdf.PdfRenderer")
        Bitmap = autoclass("android.graphics.Bitmap")
        BitmapConfig = autoclass("android.graphics.Bitmap$Config")
        CompressFormat = autoclass("android.graphics.Bitmap$CompressFormat")
        ByteArrayOutputStream = autoclass("java.io.ByteArrayOutputStream")
        File = autoclass("java.io.File")

        java_file = File(pdf_path)
        pfd = ParcelFileDescriptor.open(java_file, ParcelFileDescriptor.MODE_READ_ONLY)
        renderer = PdfRenderer(pfd)

        images = []
        total = min(renderer.getPageCount(), max_pages)
        for i in range(total):
            page = renderer.openPage(i)
            # Escala ~1.5x para buena legibilidad sin saturar RAM
            w = int(page.getWidth() * 1.5)
            h = int(page.getHeight() * 1.5)
            bmp = Bitmap.createBitmap(w, h, BitmapConfig.ARGB_8888)
            # Fondo blanco (los PDFs suelen tener fondo transparente)
            bmp.eraseColor(-1)
            page.render(bmp, None, None, 1)  # 1 = RENDER_MODE_FOR_DISPLAY
            page.close()

            stream = ByteArrayOutputStream()
            bmp.compress(CompressFormat.JPEG, 85, stream)
            raw_bytes = bytes(stream.toByteArray())
            bmp.recycle()

            images.append(Image.open(io.BytesIO(raw_bytes)))

        renderer.close()
        pfd.close()
        return images

    def _render_desktop(self, pdf_path, max_pages):
        try:
            import fitz  # PyMuPDF para pruebas en PC
            doc = fitz.open(pdf_path)
            images = []
            for i in range(min(len(doc), max_pages)):
                pix = doc[i].get_pixmap(dpi=130)
                images.append(Image.open(io.BytesIO(pix.tobytes("jpeg"))))
            return images
        except ImportError:
            raise RuntimeError("En PC instala pymupdf (`pip install pymupdf`) para probar PDFs.")

    def _run(self, pdf_path, api_key, max_pages, on_progress, on_done, on_error):
        if not api_key:
            if on_error:
                on_error("Pega tu API Key de Gemini antes de importar.")
            return
        try:
            if on_progress:
                on_progress("Renderizando páginas del PDF...")
            all_images = self._render_pages_pil(pdf_path, max_pages)
            total_pages = len(all_images)
            if total_pages == 0:
                if on_error:
                    on_error("El PDF no contiene páginas legibles.")
                return

            created_topics = 0
            created_exercises = 0
            batch_size = 2

            for start in range(0, total_pages, batch_size):
                end = min(start + batch_size, total_pages)
                if on_progress:
                    on_progress(f"IA analizando páginas {start + 1} a {end} de {total_pages}...")

                batch_imgs = all_images[start:end]
                parts = [{"text": PROMPT_EXTRACCION}]
                for pil_img in batch_imgs:
                    buf = io.BytesIO()
                    pil_img.save(buf, format="JPEG", quality=80)
                    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64}})

                data = self._call_gemini(parts, api_key)
                t_c, e_c = self._save_to_db(data, batch_imgs, start)
                created_topics += t_c
                created_exercises += e_c

            if on_done:
                on_done(created_topics, created_exercises)
        except Exception as exc:
            if on_error:
                on_error(f"Error al importar: {exc}")

    def _call_gemini(self, parts, api_key):
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash:generateContent?key={api_key}"
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw_text)

    def _save_to_db(self, data, page_images, page_offset):
        t_created = 0
        e_created = 0
        valid_cats = {"Reading", "Listening", "Speaking", "Writing", "Conversations"}

        for topic in data.get("topics", []):
            cat = topic.get("category", "Reading")
            if cat not in valid_cats:
                cat = "Reading"
            name = (topic.get("name") or "").strip()
            if not name:
                continue

            if not self.db.topic_exists(cat, name):
                topic_id = self.db.add_topic(cat, name, topic.get("description", ""))
                t_created += 1
            else:
                rows = [r for r in self.db.topics(cat) if r["name"].lower() == name.lower()]
                topic_id = rows[0]["id"]

            for idx, ex in enumerate(topic.get("exercises", [])):
                prompt = (ex.get("prompt") or "").strip()
                answer = (ex.get("answer") or "").strip()
                if not prompt or not answer:
                    continue

                img_filename = ""
                box = ex.get("image_box")
                p_idx = ex.get("page_index", 0)
                if box and len(box) == 4 and 0 <= p_idx < len(page_images):
                    img_filename = self._crop_and_save(
                        page_images[p_idx], box, f"book_p{page_offset + p_idx}_{idx}.jpg"
                    )

                self.db.add_exercise(
                    topic_id=topic_id,
                    prompt=prompt,
                    passage=ex.get("passage", ""),
                    answer=answer,
                    mode=ex.get("mode", "exact"),
                    image=img_filename,
                )
                e_created += 1

        return t_created, e_created

    def _crop_and_save(self, pil_img, box, filename):
        w, h = pil_img.size
        ymin, xmin, ymax, xmax = box
        left = max(0, int((xmin / 1000.0) * w))
        top = max(0, int((ymin / 1000.0) * h))
        right = min(w, int((xmax / 1000.0) * w))
        bottom = min(h, int((ymax / 1000.0) * h))
        if right - left < 20 or bottom - top < 20:
            return ""
        cropped = pil_img.crop((left, top, right, bottom))
        out_path = os.path.join(self.images_dir, filename)
        cropped.save(out_path, format="JPEG", quality=85)
        return filename