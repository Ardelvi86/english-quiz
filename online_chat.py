"""Cliente de chat en tiempo real para English Quiz usando Firebase REST API.

Permite que dos usuarios en celulares distintos se conecten con el mismo
código de sala (ej. JUAN-24) y practiquen inglés por texto o voz.
"""
import json
import threading
import time
import urllib.parse
import urllib.request


class OnlineChatClient:
    def __init__(self, firebase_url, token_provider=None):
        self.base_url = (firebase_url or "").strip().rstrip("/")
        self.token_provider = token_provider
        self.room_code = ""
        self.user_name = "Estudiante"
        self._running = False
        self._thread = None
        self._on_messages = None
        self._on_error = None
        self._last_snapshot = ""

    def is_configured(self):
        return self.base_url.startswith("https://")

    def _authenticated_url(self, url):
        if self.token_provider is None:
            return url
        token = self.token_provider()
        separator = "&" if "?" in url else "?"
        return "%s%sauth=%s" % (
            url, separator, urllib.parse.quote(token, safe="")
        )

    def join_room(self, room_code, user_name, on_messages, on_error=None):
        self.leave_room()
        self.room_code = room_code.strip().upper()
        self.user_name = (user_name or "Estudiante").strip()
        self._on_messages = on_messages
        self._on_error = on_error
        self._last_snapshot = ""

        if not self.is_configured():
            if on_error:
                on_error("Configura tu URL de Firebase en Manage o en main.py.")
            return

        self._running = True
        self.send_message(f"se unió a la sala {self.room_code}.", is_system=True)
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def leave_room(self):
        self._running = False

    def send_message(self, text, is_system=False):
        if not self.is_configured() or not self.room_code or not text.strip():
            return
        payload = {
            "sender": "Sistema" if is_system else self.user_name,
            "message": f"{self.user_name} {text}" if is_system else text.strip(),
            "ts": int(time.time() * 1000),
        }
        threading.Thread(target=self._post, args=(payload,), daemon=True).start()

    def _post(self, payload):
        try:
            url = self._authenticated_url(
                f"{self.base_url}/rooms/{self.room_code}.json"
            )
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception as exc:
            if self._on_error:
                self._on_error(f"Error de red al enviar: {exc}")

    def _poll_loop(self):
        while self._running:
            try:
                url = self._authenticated_url(
                    f"{self.base_url}/rooms/{self.room_code}.json"
                )
                with urllib.request.urlopen(url, timeout=10) as resp:
                    raw = resp.read().decode("utf-8")
                if raw != self._last_snapshot:
                    self._last_snapshot = raw
                    data = json.loads(raw) if raw and raw != "null" else {}
                    messages = sorted(data.values(), key=lambda x: x.get("ts", 0))[-40:]
                    if self._on_messages:
                        self._on_messages(messages)
            except Exception as exc:
                if self._on_error:
                    self._on_error(f"Sin conexión a la sala: {exc}")
            time.sleep(2.0)