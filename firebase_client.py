"""Firebase Authentication and Realtime Database REST client."""
import base64
import binascii
import json
import urllib.error
import urllib.parse
import urllib.request

from network_utils import create_ssl_context


class FirebaseError(Exception):
    """Raised when Firebase rejects a request or cannot be reached."""


_AUTH_ERRORS = {
    "EMAIL_EXISTS": "Ese correo ya está registrado.",
    "EMAIL_NOT_FOUND": "No existe una cuenta con ese correo.",
    "INVALID_EMAIL": "El correo no es válido.",
    "INVALID_PASSWORD": "La contraseña es incorrecta.",
    "INVALID_LOGIN_CREDENTIALS": "El correo o la contraseña son incorrectos.",
    "WEAK_PASSWORD": "La contraseña debe tener al menos 6 caracteres.",
    "USER_DISABLED": "La cuenta está deshabilitada.",
    "API_KEY_INVALID": "La API key de Firebase no es válida.",
}


class FirebaseClient:
    AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1"
    TOKEN_URL = "https://securetoken.googleapis.com/v1/token"

    def __init__(self, api_key, database_url):
        self.api_key = (api_key or "").strip()
        self.database_url = (database_url or "").strip().rstrip("/")

    def is_configured(self):
        return bool(self.api_key) and self.database_url.startswith("https://")

    def _require_configured(self):
        if not self.api_key:
            raise FirebaseError(
                "Falta configurar FIREBASE_WEB_API_KEY en main.py."
            )
        if not self.database_url.startswith("https://"):
            raise FirebaseError("La URL de Firebase debe comenzar con https://.")

    @staticmethod
    def _error_message(raw, fallback):
        try:
            message = json.loads(raw).get("error", {}).get("message", "")
        except (ValueError, AttributeError):
            message = ""
        if not isinstance(message, str):
            message = ""
        if message in _AUTH_ERRORS:
            return _AUTH_ERRORS[message]
        if message.startswith("WEAK_PASSWORD"):
            return _AUTH_ERRORS["WEAK_PASSWORD"]
        return "%s%s" % (fallback, (": " + message) if message else "")

    @staticmethod
    def _request(url, method="GET", payload=None, form=False):
        data = None
        headers = {}
        if payload is not None:
            if form:
                data = urllib.parse.urlencode(payload).encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                data = json.dumps(payload).encode("utf-8")
                headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            url, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(
                request, timeout=15, context=create_ssl_context()
            ) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise FirebaseError(
                FirebaseClient._error_message(body, "Firebase rechazó la solicitud")
            ) from exc
        except urllib.error.URLError as exc:
            raise FirebaseError(
                "No se pudo conectar con Firebase: %s" % exc.reason
            ) from exc
        except OSError as exc:
            raise FirebaseError("Error de red con Firebase: %s" % exc) from exc
        if not body:
            return None
        try:
            return json.loads(body)
        except ValueError as exc:
            raise FirebaseError("Firebase devolvió una respuesta no válida.") from exc

    @staticmethod
    def _request_bytes(url, method="GET", payload=None, content_type=None,
                       id_token=None):
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        if id_token:
            headers["Authorization"] = "Bearer " + id_token
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
            raise FirebaseError(
                FirebaseClient._error_message(
                    body, "Firebase Storage rechazó la solicitud"
                )
            ) from exc
        except urllib.error.URLError as exc:
            raise FirebaseError(
                "No se pudo conectar con Firebase Storage: %s" % exc.reason
            ) from exc
        except OSError as exc:
            raise FirebaseError("Error de red con Firebase Storage: %s" % exc) from exc

    def _auth_url(self, action):
        self._require_configured()
        return "%s/accounts:%s?key=%s" % (
            self.AUTH_BASE_URL,
            action,
            urllib.parse.quote(self.api_key, safe=""),
        )

    def register(self, email, password):
        return self._request(
            self._auth_url("signUp"),
            method="POST",
            payload={
                "email": email.strip(),
                "password": password,
                "returnSecureToken": True,
            },
        )

    def sign_in(self, email, password):
        return self._request(
            self._auth_url("signInWithPassword"),
            method="POST",
            payload={
                "email": email.strip(),
                "password": password,
                "returnSecureToken": True,
            },
        )

    def refresh_session(self, refresh_token):
        self._require_configured()
        url = "%s?key=%s" % (
            self.TOKEN_URL,
            urllib.parse.quote(self.api_key, safe=""),
        )
        response = self._request(
            url,
            method="POST",
            payload={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            form=True,
        )
        return {
            "idToken": response["id_token"],
            "refreshToken": response["refresh_token"],
            "localId": response["user_id"],
            "expiresIn": response["expires_in"],
        }

    def _database_url(self, path, id_token):
        self._require_configured()
        encoded_path = "/".join(
            urllib.parse.quote(part, safe="") for part in path.split("/")
        )
        url = "%s/%s.json" % (self.database_url, encoded_path)
        return "%s?auth=%s" % (
            url,
            urllib.parse.quote(id_token, safe=""),
        )

    def get_role(self, uid, id_token):
        role = self._request(
            self._database_url("roles/%s" % uid, id_token)
        )
        if self._has_admin_claim(id_token):
            return "admin"
        return role

    @staticmethod
    def _has_admin_claim(id_token):
        try:
            encoded_payload = id_token.split(".")[1]
            encoded_payload += "=" * (-len(encoded_payload) % 4)
            claims = json.loads(
                base64.urlsafe_b64decode(encoded_payload).decode("utf-8")
            )
        except (AttributeError, IndexError, UnicodeDecodeError,
                ValueError, binascii.Error):
            return False
        return isinstance(claims, dict) and claims.get("admin") is True

    def get_progress(self, uid, id_token):
        data = self._request(
            self._database_url("progress/%s/events" % uid, id_token)
        )
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise FirebaseError("Firebase devolvió datos de progreso no válidos.")
        return data

    def put_progress_event(self, uid, event_id, event, id_token):
        return self._request(
            self._database_url(
                "progress/%s/events/%s" % (uid, event_id), id_token
            ),
            method="PUT",
            payload=event,
        )

    def delete_progress_for_exercises(self, uid, deletion_cutoffs, id_token):
        events = self.get_progress(uid, id_token)
        deleted = 0
        for event_id, event in events.items():
            if not isinstance(event, dict):
                raise FirebaseError("Firebase devolvió un evento de progreso no válido.")
            exercise_key = event.get("exercise_key")
            created_at = event.get("created_at")
            if (not isinstance(exercise_key, str)
                    or not isinstance(created_at, (int, float))):
                raise FirebaseError("Firebase devolvió un evento de progreso incompleto.")
            cutoff = deletion_cutoffs.get(exercise_key)
            if cutoff is not None and created_at <= cutoff:
                self._request(
                    self._database_url(
                        "progress/%s/events/%s" % (uid, event_id), id_token
                    ),
                    method="DELETE",
                )
                deleted += 1
        return deleted

    def delete_progress(self, uid, id_token):
        return self._request(
            self._database_url("progress/%s/events" % uid, id_token),
            method="DELETE",
        )

    def get_shared_content(self, id_token):
        data = self._request(
            self._database_url("shared_content/snapshot", id_token)
        )
        if data is not None and not isinstance(data, dict):
            raise FirebaseError("Firebase devolvió una biblioteca compartida no válida.")
        return data

    def put_shared_content(self, snapshot, id_token):
        return self._request(
            self._database_url("shared_content/snapshot", id_token),
            method="PUT",
            payload=snapshot,
        )

    @staticmethod
    def _storage_object_url(bucket, object_name):
        encoded_bucket = urllib.parse.quote((bucket or "").strip(), safe="")
        encoded_name = urllib.parse.quote(object_name, safe="")
        return (
            "https://firebasestorage.googleapis.com/v0/b/%s/o/%s"
            % (encoded_bucket, encoded_name)
        )

    def upload_shared_image(self, bucket, object_name, image_bytes, id_token):
        if not bucket:
            raise FirebaseError("Configura el bucket de Firebase Storage.")
        url = (
            "https://firebasestorage.googleapis.com/v0/b/%s/o?%s"
            % (
                urllib.parse.quote(bucket.strip(), safe=""),
                urllib.parse.urlencode({"uploadType": "media", "name": object_name}),
            )
        )
        self._request_bytes(
            url, method="POST", payload=image_bytes, content_type="image/jpeg",
            id_token=id_token,
        )

    def download_shared_image(self, bucket, object_name, id_token):
        if not bucket:
            raise FirebaseError("Configura el bucket de Firebase Storage.")
        url = self._storage_object_url(bucket, object_name) + "?alt=media"
        image_bytes = self._request_bytes(url, id_token=id_token)
        if not image_bytes:
            raise FirebaseError("Firebase Storage devolvió una imagen vacía.")
        return image_bytes

    def delete_shared_image(self, bucket, object_name, id_token):
        if not bucket:
            raise FirebaseError("Configura el bucket de Firebase Storage.")
        self._request_bytes(
            self._storage_object_url(bucket, object_name),
            method="DELETE",
            id_token=id_token,
        )
