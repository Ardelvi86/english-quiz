"""Supabase Storage REST client using Firebase ID tokens for uploads."""
import base64
import binascii
import io
import json
import urllib.error
import urllib.parse
import urllib.request

from firebase_client import FirebaseError
from network_utils import create_ssl_context
from PIL import Image


class SupabaseStorageClient:
    def __init__(self, project_url, publishable_key, bucket):
        self.project_url = (project_url or "").strip().rstrip("/")
        self.publishable_key = (publishable_key or "").strip()
        self.bucket = (bucket or "").strip()

    @staticmethod
    def is_valid_project_url(project_url):
        parsed = urllib.parse.urlsplit(project_url)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.hostname.endswith(".supabase.co")
            and parsed.hostname != ".supabase.co"
            and parsed.netloc == parsed.hostname
            and not parsed.username
            and not parsed.password
            and parsed.path in ("", "/")
            and not parsed.query
            and not parsed.fragment
        )

    @staticmethod
    def is_secret_key(key):
        if key.startswith("sb_secret_"):
            return True
        parts = key.split(".")
        if len(parts) != 3:
            return False
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        try:
            claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, binascii.Error):
            return False
        return isinstance(claims, dict) and claims.get("role") in (
            "service_role", "supabase_admin",
        )

    @property
    def is_configured(self):
        return (
            self.is_valid_project_url(self.project_url)
            and bool(self.publishable_key)
            and not self.is_secret_key(self.publishable_key)
            and bool(self.bucket)
        )

    @staticmethod
    def parse_public_url(public_url):
        parsed = urllib.parse.urlsplit(public_url)
        if (parsed.scheme != "https" or not parsed.hostname
                or not parsed.hostname.endswith(".supabase.co")
                or parsed.netloc != parsed.hostname
                or parsed.username or parsed.password or parsed.query
                or parsed.fragment):
            raise ValueError("Firebase devolvió una URL de imagen no válida.")

        parts = urllib.parse.unquote(parsed.path).strip("/").split("/")
        if len(parts) < 6 or parts[:4] != [
                "storage", "v1", "object", "public"]:
            raise ValueError("Firebase devolvió una URL de imagen no válida.")
        bucket = parts[4]
        object_name = "/".join(parts[5:])
        if not bucket or not object_name:
            raise ValueError("Firebase devolvió una URL de imagen no válida.")
        return parsed.netloc, bucket, object_name

    def owns_public_url(self, public_url):
        host, bucket, _ = self.parse_public_url(public_url)
        project_host = urllib.parse.urlsplit(self.project_url).netloc
        return host == project_host and bucket == self.bucket

    def public_url(self, object_name):
        if not self.is_configured:
            raise FirebaseError(
                "Configura la URL, la clave publicable y el bucket de Supabase."
            )
        return "%s/storage/v1/object/public/%s/%s" % (
            self.project_url,
            urllib.parse.quote(self.bucket, safe=""),
            urllib.parse.quote(object_name, safe="/"),
        )

    @staticmethod
    def to_jpeg(image_bytes):
        with Image.open(io.BytesIO(image_bytes)) as image:
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            output = io.BytesIO()
            background.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()

    def _object_url(self, object_name):
        if not self.is_configured:
            raise FirebaseError(
                "Configura la URL, la clave publicable y el bucket de Supabase."
            )
        if (not object_name or object_name.startswith("/")
                or any(part in ("", ".", "..") for part in object_name.split("/"))):
            raise ValueError("La ruta de imagen de Supabase no es válida.")
        return "%s/storage/v1/object/%s/%s" % (
            self.project_url,
            urllib.parse.quote(self.bucket, safe=""),
            urllib.parse.quote(object_name, safe="/"),
        )

    def _request(self, url, method, id_token, payload=None):
        headers = {
            "apikey": self.publishable_key,
            "Authorization": "Bearer " + id_token,
        }
        if payload is not None:
            headers["Content-Type"] = "image/jpeg"
            headers["x-upsert"] = "true"
        request = urllib.request.Request(
            url, data=payload, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(
                request, timeout=30, context=create_ssl_context()
            ) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                error = json.loads(body)
                detail = error.get("message") or error.get("error") or body
            except (ValueError, AttributeError):
                detail = body or exc.reason
            raise FirebaseError(
                "Supabase Storage rechazó la solicitud (HTTP %d): %s"
                % (exc.code, detail)
            ) from exc
        except urllib.error.URLError as exc:
            raise FirebaseError(
                "No se pudo conectar con Supabase Storage: %s" % exc.reason
            ) from exc
        except OSError as exc:
            raise FirebaseError("Error de red con Supabase Storage: %s" % exc) from exc

    def upload_image(self, object_name, image_bytes, firebase_id_token):
        if not image_bytes:
            raise ValueError("No se puede subir una imagen vacía.")
        self._request(
            self._object_url(object_name),
            method="POST",
            id_token=firebase_id_token,
            payload=image_bytes,
        )
        return self.public_url(object_name)

    def delete_image(self, object_name, firebase_id_token):
        self._request(
            self._object_url(object_name),
            method="DELETE",
            id_token=firebase_id_token,
        )

    @staticmethod
    def download_public_image(public_url):
        SupabaseStorageClient.parse_public_url(public_url)
        try:
            with urllib.request.urlopen(
                public_url, timeout=30, context=create_ssl_context()
            ) as response:
                image_bytes = response.read()
        except urllib.error.HTTPError as exc:
            raise FirebaseError(
                "Supabase Storage no pudo descargar la imagen (HTTP %d)."
                % exc.code
            ) from exc
        except urllib.error.URLError as exc:
            raise FirebaseError(
                "No se pudo conectar con Supabase Storage: %s" % exc.reason
            ) from exc
        except OSError as exc:
            raise FirebaseError("Error de red con Supabase Storage: %s" % exc) from exc
        if not image_bytes:
            raise FirebaseError("Supabase Storage devolvió una imagen vacía.")
        return image_bytes
