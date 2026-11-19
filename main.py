"""English Quiz - App completa de aprendizaje de inglés (Nivel A1).

Incluye:
1. Práctica guiada (Reading, Listening, Speaking, Writing, Conversations) con imágenes.
2. Evaluación (Quiz) por unidad o mixta sin pistas.
3. Conversación en línea con amigo (chat en tiempo real + voz).
4. Importador automático de libros PDF con IA en Manage topics.
"""
import hashlib
import json
import os
import random
import re
import sqlite3
import threading
import time
import unicodedata
import uuid

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.utils import platform
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.widget import Widget

if platform not in ("android", "ios"):
    Window.size = (400, 740)
else:
    Window.softinput_mode = "below_target"

DB_NAME = "english_quiz.db"
SEED_VERSION = 8
EXAM_QUESTION_COUNT = 25
# Opcional: pega aquí tu URL de Firebase Realtime Database (ej. "https://mi-app-default-rtdb.firebaseio.com")
FIREBASE_DB_URL = "https://english-quiz-app-3f3b3-default-rtdb.firebaseio.com/"
FIREBASE_WEB_API_KEY = "AIzaSyAcBVAeuIQTfqpwxqD9OXqEBLDtTOKTGiw"
FIREBASE_STORAGE_BUCKET = "english-quiz-app-3f3b3.firebaseapp.com"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "assets", "audio")
BUNDLED_IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")
CATEGORIES = ["Reading", "Listening", "Speaking", "Writing", "Conversations"]

DESCRIPTIONS = {
    "Reading": "Lee el texto y responde la pregunta.",
    "Listening": "Toca Play audio, escucha con atención y escribe lo que se pide.",
    "Speaking": "Escucha el modelo, dilo en voz alta y escribe lo que dijiste.",
    "Writing": "Lee la regla o ejemplo y completa la palabra o frase.",
    "Conversations": "Completa el diálogo y practica con un compañero.",
}

BG = (0.043, 0.059, 0.114, 1)
PRIMARY = (0.30, 0.62, 0.98, 1)
SURFACE = (0.090, 0.118, 0.196, 1)
SURFACE2 = (0.125, 0.157, 0.247, 1)
TEXT = (0.95, 0.97, 1, 1)
OK_COLOR = (0.35, 0.88, 0.62, 1)
BAD_COLOR = (1, 0.66, 0.36, 1)
INFO_COLOR = (0.62, 0.80, 1, 1)

AREA_COLORS = {
    "Reading": (0.20, 0.47, 0.93, 1),
    "Listening": (0.55, 0.36, 0.96, 1),
    "Speaking": (0.13, 0.67, 0.50, 1),
    "Writing": (0.95, 0.55, 0.20, 1),
    "Conversations": (0.08, 0.64, 0.74, 1),
}

CONVERSATION_PROMPTS = [
    "Unit 1: Ask your friend's name, occupation, and how to spell their last name.",
    "Unit 2: Introduce a friend and ask for their phone number or e-mail.",
    "Unit 3: Ask how to get to the bank or pharmacy from your house.",
    "Unit 4: Describe two people in your family (age, appearance, occupation).",
    "Unit 5: Invite your friend to a movie or dinner and agree on the time.",
    "Unit 6: Roleplay in a clothing store asking for colors and sizes.",
    "Unit 7: Talk about your typical weekend and who does chores at home.",
]

Window.clearcolor = BG


# --------------------------------------------------------------------------
# Componentes visuales
# --------------------------------------------------------------------------
class RBtn(Button):
    bg = ListProperty([0.20, 0.47, 0.93, 1])


class Tile(Button):
    bg = ListProperty([0.20, 0.47, 0.93, 1])


class ModeCard(Button):
    bg = ListProperty([0.20, 0.47, 0.93, 1])


class LoginArtwork(KivyImage):
    def __init__(self, **kwargs):
        kwargs.setdefault(
            "source", os.path.join(BUNDLED_IMAGE_DIR, "login_travel.png")
        )
        super().__init__(**kwargs)


class Card(BoxLayout):
    bg = ListProperty([0.090, 0.118, 0.196, 1])


class Banner(Label):
    bg = ListProperty([0, 0, 0, 0])


class SoftBar(Widget):
    value = NumericProperty(0)
    maximum = NumericProperty(1)
    fill = ListProperty([0.30, 0.62, 0.98, 1])


class RSpinner(Spinner):
    bg = ListProperty([0.125, 0.157, 0.247, 1])


class SpinnerOpt(SpinnerOption):
    pass


class StatRow(BoxLayout):
    title = StringProperty("")
    detail = StringProperty("")
    value = NumericProperty(0)
    fill = ListProperty([0.30, 0.62, 0.98, 1])


class StatHero(BoxLayout):
    pct = StringProperty("0%")
    detail = StringProperty("")


class ChatBubble(BoxLayout):
    sender = StringProperty("")
    msg = StringProperty("")
    bubble_bg = ListProperty([0.125, 0.157, 0.247, 1])


# --------------------------------------------------------------------------
# Carga de módulos del proyecto
# --------------------------------------------------------------------------
from book_units import BOOK_UNITS  # noqa: E402
from firebase_client import FirebaseClient, FirebaseError  # noqa: E402
from pdf_importer import BookImporter  # noqa: E402
from online_chat import OnlineChatClient  # noqa: E402

SEED = {cat: [] for cat in CATEGORIES}
for _cat, _topics in BOOK_UNITS.items():
    SEED[_cat].extend(_topics)

try:
    from units_data import EXTRA_UNITS_3_4  # noqa: E402
    for _cat, _topics in EXTRA_UNITS_3_4.items():
        SEED[_cat].extend(_topics)
except ImportError:
    pass


# --------------------------------------------------------------------------
# Utilidades de validación
# --------------------------------------------------------------------------
def normalize(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"[^\w\s':-]", " ", text.replace("’", "'"))
    return re.sub(r"\s+", " ", text).strip()


def alternatives(expected):
    return [a.strip() for a in (expected or "").split("|") if a.strip()]


def is_correct(given, expected, mode="exact"):
    given_n = normalize(given)
    if not given_n:
        return False
    for alt in alternatives(expected):
        alt_n = normalize(alt)
        if not alt_n:
            continue
        if mode == "contains":
            if re.search(r"(^|\s)" + re.escape(alt_n) + r"(\s|$)", given_n):
                return True
        elif given_n == alt_n:
            return True
    return False


# --------------------------------------------------------------------------
# KV
# --------------------------------------------------------------------------
KV = r"""
#:import dp kivy.metrics.dp
#:set C_BG (0.043, 0.059, 0.114, 1)
#:set C_SURFACE (0.090, 0.118, 0.196, 1)
#:set C_SURFACE2 (0.125, 0.157, 0.247, 1)
#:set C_LINE (0.20, 0.25, 0.38, 1)
#:set C_TEXT (0.95, 0.97, 1, 1)
#:set C_MUTED (0.62, 0.69, 0.80, 1)
#:set C_PRIMARY (0.30, 0.62, 0.98, 1)
#:set INFO_COLOR (0.62, 0.80, 1, 1)

<Page@BoxLayout>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(12)
    canvas.before:
        Color:
            rgba: C_BG
        Rectangle:
            pos: self.pos
            size: self.size

<WrapLabel@Label>:
    size_hint_y: None
    height: (self.texture_size[1] + dp(10)) if self.text else 0
    text_size: self.width, None
    halign: 'left'
    valign: 'middle'
    color: C_TEXT

<Section@Label>:
    size_hint_y: None
    height: dp(26)
    bold: True
    font_size: '12sp'
    color: C_MUTED
    text_size: self.size
    halign: 'left'
    valign: 'bottom'

<Field@TextInput>:
    size_hint_y: None
    height: dp(50)
    multiline: False
    font_size: '16sp'
    background_normal: ''
    background_active: ''
    background_color: 0, 0, 0, 0
    foreground_color: C_TEXT
    hint_text_color: C_MUTED
    cursor_color: C_PRIMARY
    selection_color: 0.30, 0.62, 0.98, 0.35
    padding: [dp(14), dp(12), dp(14), dp(8)]
    canvas.before:
        Color:
            rgba: C_SURFACE2
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text and not self.focus else self.foreground_color)
    canvas.after:
        Color:
            rgba: C_PRIMARY if self.focus else C_LINE
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(12))
            width: 1.1
<RBtn>:
    size_hint_y: None
    height: dp(50)
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 1, 1, 1, 1
    bold: True
    font_size: '15sp'
    canvas.before:
        Color:
            rgba: self.bg if self.state == 'normal' else (self.bg[0] * .78, self.bg[1] * .78, self.bg[2] * .78, self.bg[3])
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]

<Card>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: dp(16)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]

<Banner>:
    size_hint_y: None
    height: (self.texture_size[1] + dp(26)) if self.text else 0
    text_size: self.width - dp(28), None
    halign: 'left'
    valign: 'middle'
    font_size: '15sp'
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<SoftBar>:
    canvas:
        Color:
            rgba: C_SURFACE2
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]
        Color:
            rgba: self.fill
        RoundedRectangle:
            pos: self.pos
            size: (max(self.width * min(self.value / max(self.maximum, 1), 1), self.height), self.height) if self.value > 0 else (0, self.height)
            radius: [self.height / 2]

<RSpinner>:
    size_hint_y: None
    height: dp(50)
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: C_TEXT
    font_size: '15sp'
    option_cls: 'SpinnerOpt'
    text_size: self.width - dp(48), self.height
    halign: 'left'
    valign: 'middle'
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: C_MUTED
        Triangle:
            points: [self.right - dp(32), self.center_y + dp(3), self.right - dp(20), self.center_y + dp(3), self.right - dp(26), self.center_y - dp(4)]

<SpinnerOpt>:
    background_normal: ''
    background_down: ''
    background_color: C_SURFACE2 if self.state == 'normal' else C_LINE
    color: C_TEXT
    size_hint_y: None
    height: dp(46)

<Tile>:
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 1, 1, 1, 1
    markup: True
    halign: 'left'
    valign: 'bottom'
    text_size: self.width - dp(32), self.height - dp(32)
    canvas.before:
        Color:
            rgba: self.bg if self.state == 'normal' else (self.bg[0] * .8, self.bg[1] * .8, self.bg[2] * .8, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(20)]
        Color:
            rgba: 1, 1, 1, 0.16
        Ellipse:
            pos: self.right - dp(70), self.top - dp(70)
            size: dp(50), dp(50)

<ModeCard>:
    size_hint_y: None
    height: dp(96)
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: 1, 1, 1, 1
    markup: True
    halign: 'left'
    valign: 'middle'
    text_size: self.width - dp(40), self.height - dp(24)
    canvas.before:
        Color:
            rgba: self.bg if self.state == 'normal' else (self.bg[0] * .82, self.bg[1] * .82, self.bg[2] * .82, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(20)]
        Color:
            rgba: 1, 1, 1, 0.12
        Ellipse:
            pos: self.right - dp(76), self.center_y - dp(28)
            size: dp(56), dp(56)

<ChatBubble>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: dp(12)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: self.bubble_bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
    Label:
        text: root.sender
        size_hint_y: None
        height: dp(18)
        font_size: '12sp'
        bold: True
        color: C_PRIMARY
        text_size: self.width, None
        halign: 'left'
    Label:
        text: root.msg
        size_hint_y: None
        height: self.texture_size[1] + dp(4)
        font_size: '15sp'
        color: C_TEXT
        text_size: self.width, None
        halign: 'left'

<StatRow>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(80)
    padding: dp(16)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: C_SURFACE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]
    BoxLayout:
        Label:
            text: root.title
            bold: True
            font_size: '16sp'
            color: C_TEXT
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        Label:
            text: root.detail
            font_size: '13sp'
            color: C_MUTED
            text_size: self.size
            halign: 'right'
            valign: 'middle'
    SoftBar:
        size_hint_y: None
        height: dp(8)
        value: root.value
        maximum: 100
        fill: root.fill

<StatHero>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(140)
    padding: dp(18)
    spacing: dp(2)
    canvas.before:
        Color:
            rgba: 0.18, 0.42, 0.88, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(22)]
        Color:
            rgba: 1, 1, 1, 0.10
        Ellipse:
            pos: self.right - dp(104), self.top - dp(104)
            size: dp(86), dp(86)
    Label:
        text: 'RESULTADO TOTAL'
        bold: True
        font_size: '12sp'
        color: 0.86, 0.92, 1, 1
        text_size: self.size
        halign: 'left'
        valign: 'middle'
    Label:
        text: root.pct
        bold: True
        font_size: '46sp'
        color: 1, 1, 1, 1
        text_size: self.size
        halign: 'left'
        valign: 'middle'
    Label:
        text: root.detail
        font_size: '14sp'
        color: 0.86, 0.92, 1, 1
        text_size: self.size
        halign: 'left'
        valign: 'middle'

# ---------------------------------------------------------------- AUTENTICACIÓN
<LoginArtwork>:
    size_hint_y: None
    height: dp(220)
    fit_mode: 'cover'

<LoginScreen>:
    Page:
        ScrollView:
            do_scroll_x: False
            bar_width: 0
            scroll_y: 1
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: [0, dp(12), 0, dp(12)]
                LoginArtwork:
                Label:
                    text: 'English Quiz'
                    size_hint_y: None
                    height: dp(42)
                    font_size: '30sp'
                    bold: True
                    color: C_TEXT
                Label:
                    text: 'Inicia sesión para continuar'
                    size_hint_y: None
                    height: dp(24)
                    font_size: '15sp'
                    color: C_MUTED
                Field:
                    id: email
                    hint_text: 'Correo electrónico'
                    multiline: False
                Field:
                    id: password
                    hint_text: 'Contraseña'
                    password: True
                    multiline: False
                Banner:
                    id: status
                    text: ''
                RBtn:
                    id: login_button
                    text: 'Iniciar sesión'
                    bg: C_PRIMARY
                    on_release: root.login()
                RBtn:
                    text: 'Crear cuenta de usuario'
                    bg: C_SURFACE2
                    on_release: root.open_registration()

<RegisterScreen>:
    Page:
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(14)
            padding: [0, dp(24), 0, dp(20)]
            RBtn:
                text: '<'
                size_hint_y: None
                height: dp(48)
                bg: C_SURFACE2
                on_release: root.go_login()
            Label:
                text: 'Registro de usuario'
                size_hint_y: None
                height: dp(42)
                font_size: '26sp'
                bold: True
                color: C_TEXT
            Field:
                id: email
                hint_text: 'Correo electrónico'
                multiline: False
            Field:
                id: password
                hint_text: 'Contraseña (mínimo 6 caracteres)'
                password: True
                multiline: False
            Field:
                id: confirm_password
                hint_text: 'Repite la contraseña'
                password: True
                multiline: False
            Banner:
                id: status
                text: ''
            RBtn:
                id: register_button
                text: 'Crear cuenta'
                bg: C_PRIMARY
                on_release: root.register()

# ---------------------------------------------------------------- PANEL PRINCIPAL
<HomeScreen>:
    Page:
        ScrollView:
            do_scroll_x: False
            bar_width: 0
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(14)
                padding: [0, 0, 0, dp(12)]
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(76)
                    BoxLayout:
                        size_hint_y: None
                        height: dp(42)
                        Label:
                            text: 'English Quiz'
                            bold: True
                            font_size: '30sp'
                            color: C_TEXT
                            text_size: self.size
                            halign: 'left'
                            valign: 'middle'
                        RBtn:
                            text: 'Salir'
                            size_hint_x: None
                            width: dp(72)
                            height: dp(38)
                            bg: C_SURFACE2
                            on_release: app.logout()
                    Label:
                        id: signed_in_user
                        text: ''
                        font_size: '13sp'
                        color: C_MUTED
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'
                        size_hint_y: None
                        height: dp(28)
                Card:
                    BoxLayout:
                        size_hint_y: None
                        height: dp(62)
                        spacing: dp(10)
                        BoxLayout:
                            orientation: 'vertical'
                            Label:
                                text: 'TU PROGRESO GENERAL'
                                bold: True
                                font_size: '12sp'
                                color: C_MUTED
                                text_size: self.size
                                halign: 'left'
                                valign: 'middle'
                            Label:
                                id: home_pct
                                text: '0%'
                                bold: True
                                font_size: '32sp'
                                color: C_TEXT
                                text_size: self.size
                                halign: 'left'
                                valign: 'middle'
                        RBtn:
                            text: 'Estadísticas'
                            size_hint_x: None
                            width: dp(112)
                            height: dp(40)
                            pos_hint: {'center_y': .5}
                            bg: C_SURFACE2
                            on_release: root.go('stats')
                    Label:
                        id: home_detail
                        text: ''
                        size_hint_y: None
                        height: dp(20)
                        font_size: '13sp'
                        color: C_MUTED
                        text_size: self.size
                        halign: 'left'
                        valign: 'middle'
                    SoftBar:
                        id: home_bar
                        size_hint_y: None
                        height: dp(8)
                        fill: C_PRIMARY
                Banner:
                    id: home_sync_status
                    text: ''
                    size_hint_y: None
                    height: dp(26)
                    font_size: '12sp'
                Section:
                    text: '¿QUÉ QUIERES HACER HOY?'
                ModeCard:
                    text: '[b][size=20sp]1. Práctica Guiada[/size][/b]\n[size=13sp][color=dfe9f7]Aprende con ejemplos, reglas, audio e imágenes[/color][/size]'
                    bg: 0.20, 0.47, 0.93, 1
                    on_release: root.go('practice_hub')
                ModeCard:
                    text: '[b][size=20sp]2. Evaluación (Quiz)[/size][/b]\n[size=13sp][color=dfe9f7]Ponte a prueba • mínimo 25 preguntas[/color][/size]'
                    bg: 0.55, 0.36, 0.96, 1
                    on_release: root.go('exam')
                ModeCard:
                    text: '[b][size=20sp]3. Conversación Online[/size][/b]\n[size=13sp][color=dfe9f7]Sala con código de amigo • Chat y voz a distancia[/color][/size]'
                    bg: 0.13, 0.67, 0.50, 1
                    on_release: root.go('chat')

# ---------------------------------------------------------------- HUB DE PRÁCTICA
<PracticeHubScreen>:
    Page:
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(12)
            RBtn:
                text: '<'
                size_hint_x: None
                width: dp(48)
                height: dp(48)
                font_size: '20sp'
                bg: C_SURFACE2
                on_release: root.go_back()
            Label:
                text: 'Práctica por Áreas'
                font_size: '22sp'
                bold: True
                color: C_TEXT
                text_size: self.size
                halign: 'left'
                valign: 'middle'
        ScrollView:
            do_scroll_x: False
            bar_width: 0
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [0, dp(4), 0, dp(12)]
                Section:
                    text: 'ELIGE UN APARTADO DEL LIBRO'
                GridLayout:
                    id: practice_grid
                    cols: 2
                    spacing: dp(12)
                    size_hint_y: None
                    height: self.minimum_height
                    row_default_height: dp(112)
                    row_force_default: True
                    Tile:
                        text: '[b][size=19sp]Reading[/size][/b]\n[size=12sp][color=dfe9f7]Lectura[/color][/size]'
                        bg: 0.20, 0.47, 0.93, 1
                        on_release: root.open_area('Reading')
                    Tile:
                        text: '[b][size=19sp]Listening[/size][/b]\n[size=12sp][color=dfe9f7]Escucha[/color][/size]'
                        bg: 0.55, 0.36, 0.96, 1
                        on_release: root.open_area('Listening')
                    Tile:
                        text: '[b][size=19sp]Speaking[/size][/b]\n[size=12sp][color=dfe9f7]Habla[/color][/size]'
                        bg: 0.13, 0.67, 0.50, 1
                        on_release: root.open_area('Speaking')
                    Tile:
                        text: '[b][size=19sp]Writing[/size][/b]\n[size=12sp][color=dfe9f7]Escritura[/color][/size]'
                        bg: 0.95, 0.55, 0.20, 1
                        on_release: root.open_area('Writing')
                    Tile:
                        text: '[b][size=19sp]Conversations[/size][/b]\n[size=12sp][color=dfe9f7]Diálogos[/color][/size]'
                        bg: 0.08, 0.64, 0.74, 1
                        on_release: root.open_area('Conversations')
                    Tile:
                        id: manage_pdf_button
                        text: '[b][size=19sp]Manage / PDF[/size][/b]\n[size=12sp][color=dfe9f7]Importar y administrar ejercicios[/color][/size]'
                        bg: 0.30, 0.35, 0.46, 1
                        size_hint_y: None
                        height: dp(112)
                        opacity: 0
                        disabled: True
                        on_release: root.open_admin()

# ---------------------------------------------------------------- PRÁCTICA DE ÁREA
<AreaScreen>:
    Page:
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(12)
            RBtn:
                text: '<'
                size_hint_x: None
                width: dp(48)
                height: dp(48)
                font_size: '20sp'
                bg: C_SURFACE2
                on_release: root.go_back()
            Label:
                id: area_title
                text: 'Practice'
                font_size: '22sp'
                bold: True
                color: C_TEXT
                text_size: self.size
                halign: 'left'
                valign: 'middle'
        WrapLabel:
            id: instruction
            text: ''
            color: C_MUTED
            font_size: '14sp'
        RSpinner:
            id: topic_spinner
            text: 'Select a topic'
            values: []
            on_text: root.load_topic(self.text)
        Label:
            id: progress
            text: ''
            size_hint_y: None
            height: dp(20)
            font_size: '13sp'
            color: C_MUTED
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        SoftBar:
            id: bar
            size_hint_y: None
            height: dp(8)
            maximum: 1
            value: 0
            fill: C_PRIMARY
        ScrollView:
            do_scroll_x: False
            bar_width: dp(3)
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [0, dp(4), 0, dp(16)]
                Card:
                    spacing: dp(10)
                    Image:
                        id: ex_image
                        source: ''
                        size_hint_y: None
                        height: 0
                        opacity: 0
                        allow_stretch: True
                        keep_ratio: True
                    WrapLabel:
                        id: prompt
                        text: 'Tu ejercicio aparecerá aquí.'
                        color: C_TEXT
                        font_size: '19sp'
                        bold: True
                    WrapLabel:
                        id: passage
                        text: ''
                        color: C_MUTED
                        font_size: '15sp'
                BoxLayout:
                    id: audio_row
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(10)
                    RBtn:
                        id: audio_button
                        text: 'Play audio'
                        bg: 0.45, 0.30, 0.85, 1
                        on_release: root.play_audio()
                    RBtn:
                        text: 'Slow'
                        size_hint_x: None
                        width: dp(96)
                        bg: C_SURFACE2
                        color: 0.75, 0.60, 1, 1
                        on_release: root.play_audio(True)
                Field:
                    id: answer
                    hint_text: 'Escribe tu respuesta aquí...'
                    multiline: True
                    height: dp(96)
                RBtn:
                    id: check_btn
                    text: 'Check answer'
                    bg: C_PRIMARY
                    on_release: root.check_answer()
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
                    spacing: dp(10)
                    RBtn:
                        text: 'Show answer'
                        bg: C_SURFACE2
                        on_release: root.show_answer()
                    RBtn:
                        text: 'Next  >'
                        bg: C_SURFACE2
                        color: C_PRIMARY
                        on_release: root.next_exercise()
                RBtn:
                    id: delete_exercise_button
                    text: 'Eliminar este ejercicio'
                    bg: 0.62, 0.20, 0.22, 1
                    size_hint_y: None
                    height: 0
                    opacity: 0
                    disabled: True
                    on_release: root.confirm_delete_current_exercise()
                Banner:
                    id: feedback
                    text: ''

# ---------------------------------------------------------------- MODO EVALUACIÓN (QUIZ)
<ExamScreen>:
    Page:
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(12)
            RBtn:
                text: '<'
                size_hint_x: None
                width: dp(48)
                height: dp(48)
                font_size: '20sp'
                bg: C_SURFACE2
                on_release: root.go_home()
            Label:
                text: 'Evaluación (Quiz)'
                font_size: '22sp'
                bold: True
                color: C_TEXT
                text_size: self.size
                halign: 'left'
                valign: 'middle'
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(10)
            RSpinner:
                id: unit_spinner
                text: 'Todas las Unidades (Mixto)'
                values: ['Todas las Unidades (Mixto)', 'Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5', 'Unit 6', 'Unit 7']
            RBtn:
                text: 'Comenzar Evaluación (25 preguntas)'
                bg: 0.55, 0.36, 0.96, 1
                on_release: root.start_exam()
        Label:
            id: exam_progress
            text: ''
            size_hint_y: None
            height: dp(20)
            font_size: '13sp'
            color: C_MUTED
            text_size: self.size
            halign: 'left'
            valign: 'middle'
        SoftBar:
            id: exam_bar
            size_hint_y: None
            height: dp(8)
            maximum: 10
            value: 0
            fill: 0.55, 0.36, 0.96, 1
        ScrollView:
            do_scroll_x: False
            bar_width: dp(3)
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [0, dp(4), 0, dp(16)]
                Card:
                    Image:
                        id: exam_image
                        source: ''
                        size_hint_y: None
                        height: 0
                        opacity: 0
                        allow_stretch: True
                        keep_ratio: True
                    WrapLabel:
                        id: exam_cat
                        text: 'MODO EXAMEN'
                        color: 0.75, 0.60, 1, 1
                        font_size: '12sp'
                        bold: True
                    WrapLabel:
                        id: exam_prompt
                        text: 'Selecciona una unidad arriba y pulsa Comenzar Evaluación.'
                        color: C_TEXT
                        font_size: '19sp'
                        bold: True
                    WrapLabel:
                        id: exam_passage
                        text: ''
                        color: C_MUTED
                        font_size: '15sp'
                RBtn:
                    id: exam_audio_btn
                    text: 'Escuchar audio'
                    bg: 0.45, 0.30, 0.85, 1
                    disabled: True
                    opacity: 0
                    height: 0
                    on_release: root.play_exam_audio()
                Field:
                    id: exam_answer
                    hint_text: 'Tu respuesta...'
                    disabled: True
                RBtn:
                    id: exam_submit_btn
                    text: 'Siguiente pregunta  >'
                    bg: 0.55, 0.36, 0.96, 1
                    disabled: True
                    on_release: root.submit_and_next()
                Banner:
                    id: exam_result
                    text: ''

# ---------------------------------------------------------------- MODO CONVERSACIÓN EN LÍNEA
<ChatScreen>:
    Page:
        padding: [dp(16), dp(16), dp(16), dp(96)]
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(12)
            RBtn:
                text: '<'
                size_hint_x: None
                width: dp(48)
                height: dp(48)
                font_size: '20sp'
                bg: C_SURFACE2
                on_release: root.go_home()
            Label:
                text: 'Conversación Online'
                font_size: '21sp'
                bold: True
                color: C_TEXT
                text_size: self.size
                halign: 'left'
                valign: 'middle'
        Card:
            padding: dp(12)
            spacing: dp(8)
            BoxLayout:
                size_hint_y: None
                height: dp(44)
                spacing: dp(6)
                Field:
                    id: my_name
                    hint_text: 'Tu nombre'
                    height: dp(44)
                Field:
                    id: friend_code
                    hint_text: 'Código (ej. JUAN-24)'
                    height: dp(44)
                RBtn:
                    text: 'Unirse'
                    size_hint_x: None
                    width: dp(80)
                    height: dp(44)
                    bg: 0.13, 0.67, 0.50, 1
                    on_release: root.connect_friend()
            WrapLabel:
                id: topic_guide
                text: 'Tema sugerido: Unit 1 - Ask your friend name and occupation.'
                color: INFO_COLOR
                font_size: '13sp'
            RBtn:
                text: 'Cambiar tema del libro'
                height: dp(36)
                font_size: '13sp'
                bg: C_SURFACE2
                on_release: root.next_topic_guide()
        ScrollView:
            id: chat_scroll
            do_scroll_x: False
            bar_width: dp(3)
            BoxLayout:
                id: chat_box
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
                padding: [0, dp(4), 0, dp(8)]
        Banner:
            id: mic_status
            text: ''
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(8)
            RBtn:
                id: mic_btn
                text: 'Voz'
                size_hint_x: None
                width: dp(68)
                bg: 0.85, 0.28, 0.36, 1
                on_release: root.start_voice_input()
            Field:
                id: chat_input
                hint_text: 'Escribe o dicta en inglés...'
            RBtn:
                text: 'Enviar'
                size_hint_x: None
                width: dp(82)
                bg: C_PRIMARY
                on_release: root.send_message()

# ---------------------------------------------------------------- PROGRESO
<StatsScreen>:
    Page:
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(12)
            RBtn:
                text: '<'
                size_hint_x: None
                width: dp(48)
                height: dp(48)
                font_size: '20sp'
                bg: C_SURFACE2
                on_release: root.go_home()
            Label:
                text: 'My progress'
                font_size: '22sp'
                bold: True
                color: C_TEXT
                text_size: self.size
                halign: 'left'
                valign: 'middle'
        ScrollView:
            do_scroll_x: False
            bar_width: dp(3)
            BoxLayout:
                id: stats_box
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [0, dp(4), 0, dp(8)]
        Banner:
            id: stats_status
            text: ''
        RBtn:
            id: reset_progress_button
            text: 'Reset progress'
            bg: 0.62, 0.20, 0.22, 1
            size_hint_y: None
            height: 0
            opacity: 0
            disabled: True
            on_release: root.confirm_reset()

# ---------------------------------------------------------------- ADMINISTRACIÓN + PDF IA + FIREBASE
<AdminScreen>:
    Page:
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(12)
            RBtn:
                text: '<'
                size_hint_x: None
                width: dp(48)
                height: dp(48)
                font_size: '20sp'
                bg: C_SURFACE2
                on_release: root.go_back()
            Label:
                text: 'Manage & Importar PDF'
                font_size: '21sp'
                bold: True
                color: C_TEXT
                text_size: self.size
                halign: 'left'
                valign: 'middle'
        ScrollView:
            do_scroll_x: False
            bar_width: dp(3)
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [0, dp(4), 0, dp(24)]
                Card:
                    Section:
                        text: 'FIREBASE REALTIME DATABASE Y STORAGE'
                    Field:
                        id: firebase_url_input
                        hint_text: 'https://tu-proyecto-default-rtdb.firebaseio.com'
                    Field:
                        id: firebase_storage_bucket_input
                        hint_text: 'Bucket, por ejemplo tu-proyecto.firebasestorage.app'
                    RBtn:
                        text: 'Guardar configuración Firebase'
                        bg: C_SURFACE2
                        on_release: root.save_firebase_url()
                Card:
                    Section:
                        text: 'IMPORTAR LIBRO PDF AUTOMÁTICAMENTE (IA)'
                    WrapLabel:
                        text: 'Sube un PDF desde tu celular: la IA extraerá las lecciones, recortará las imágenes y creará los ejercicios y exámenes.'
                        color: C_MUTED
                        font_size: '13sp'
                    Field:
                        id: gemini_key
                        hint_text: 'Pega tu Gemini API Key (se guarda aquí)'
                        password: True
                    Field:
                        id: max_pages_input
                        hint_text: 'Máximo de páginas a procesar (ej. 10)'
                        text: '10'
                        input_filter: 'int'
                    RBtn:
                        id: import_pdf_btn
                        text: 'Seleccionar libro PDF e Importar'
                        bg: 0.13, 0.67, 0.50, 1
                        on_release: root.pick_and_import_pdf()
                    Banner:
                        id: status
                        text: 'Pega tu API Key de Gemini para importar el libro.'
                        color: C_MUTED
                Card:
                    Section:
                        text: 'ÁREA DE APRENDIZAJE (MANUAL)'
                    RSpinner:
                        id: category
                        text: 'Reading'
                        values: ['Reading', 'Listening', 'Speaking', 'Writing', 'Conversations']
                        on_text: root.refresh_topics()
                Card:
                    Section:
                        text: 'NUEVO TEMA MANUAL'
                    Field:
                        id: topic_name
                        hint_text: 'Nombre del tema (ej. Unit 8 - Home)'
                    Field:
                        id: topic_description
                        hint_text: 'Descripción corta'
                        multiline: True
                        height: dp(76)
                    RBtn:
                        text: 'Save topic'
                        bg: C_PRIMARY
                        on_release: root.save_topic()
                Card:
                    Section:
                        text: 'EJERCICIOS DEL TEMA'
                    RSpinner:
                        id: topic_pick
                        text: 'Select a topic'
                        values: []
                        on_text: root.refresh_exercises()
                    RSpinner:
                        id: exercise_pick
                        text: 'Selecciona un ejercicio'
                        values: []
                    RBtn:
                        text: 'Cargar ejercicio para editar'
                        bg: C_SURFACE2
                        on_release: root.load_selected_exercise()
                    Field:
                        id: ex_prompt
                        hint_text: 'Pregunta / instrucción'
                        multiline: True
                        height: dp(76)
                    Field:
                        id: ex_passage
                        hint_text: 'Texto, pista o transcripción'
                        multiline: True
                        height: dp(76)
                    Field:
                        id: ex_answer
                        hint_text: 'Respuesta (alternativas con |)'
                    RSpinner:
                        id: ex_mode
                        text: 'exact'
                        values: ['exact', 'contains']
                    RBtn:
                        text: 'Añadir ejercicio'
                        bg: C_PRIMARY
                        on_release: root.save_exercise()
                    RBtn:
                        text: 'Guardar cambios'
                        bg: C_SURFACE2
                        on_release: root.update_selected_exercise()
                    RBtn:
                        text: 'Eliminar ejercicio seleccionado'
                        bg: 0.62, 0.20, 0.22, 1
                        on_release: root.confirm_delete_exercise()
                RBtn:
                    text: 'Delete selected topic'
                    bg: 0.62, 0.20, 0.22, 1
                    on_release: root.confirm_delete_topic()
"""


# --------------------------------------------------------------------------
# Base de datos SQLite
# --------------------------------------------------------------------------
class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._progress_lock = threading.RLock()
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.migrate()
        self.seed()

    def create_tables(self):
        c = self.conn
        c.execute("""CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            source TEXT NOT NULL DEFAULT 'admin',
            UNIQUE(category, name))""")
        c.execute("""CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            passage TEXT DEFAULT '',
            answer TEXT NOT NULL,
            audio_file TEXT DEFAULT '',
            mode TEXT DEFAULT 'exact',
            image_file TEXT DEFAULT '',
            source TEXT NOT NULL DEFAULT 'admin',
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE)""")
        c.execute("""CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE)""")
        c.execute("""CREATE TABLE IF NOT EXISTS progress_events (
            user_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            category TEXT NOT NULL,
            correct INTEGER NOT NULL,
            exercise_key TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            synced INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(user_id, event_id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS progress_deletions (
            user_id TEXT NOT NULL,
            exercise_key TEXT NOT NULL,
            deleted_before INTEGER NOT NULL,
            PRIMARY KEY(user_id, exercise_key))""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS pdf_imported_exercises (
            source_hash TEXT NOT NULL,
            exercise_id INTEGER NOT NULL UNIQUE,
            PRIMARY KEY(source_hash, exercise_id),
            FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE)""")
        c.execute("""CREATE TABLE IF NOT EXISTS pdf_imported_topics (
            source_hash TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            PRIMARY KEY(source_hash, topic_id),
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE)""")
        c.commit()

    def migrate(self):
        topic_cols = {
            row["name"] for row in
            self.conn.execute("PRAGMA table_info(topics)").fetchall()
        }
        exercise_cols = {
            row["name"] for row in
            self.conn.execute("PRAGMA table_info(exercises)").fetchall()
        }
        source_migration = "source" not in topic_cols or "source" not in exercise_cols
        if "source" not in topic_cols:
            self.conn.execute(
                "ALTER TABLE topics ADD COLUMN source TEXT NOT NULL DEFAULT 'admin'"
            )
        if "image_file" not in exercise_cols:
            self.conn.execute("ALTER TABLE exercises ADD COLUMN image_file TEXT DEFAULT ''")
        if "source" not in exercise_cols:
            self.conn.execute(
                "ALTER TABLE exercises ADD COLUMN source TEXT NOT NULL DEFAULT 'admin'"
            )

        if source_migration:
            for category, seed_topics in SEED.items():
                for name, _, seed_exercises in seed_topics:
                    self.conn.execute(
                        "UPDATE topics SET source='builtin' "
                        "WHERE category=? AND name=?",
                        (category, name),
                    )
                    row = self.conn.execute(
                        "SELECT id FROM topics WHERE category=? AND name=?",
                        (category, name),
                    ).fetchone()
                    if row is None:
                        continue
                    topic_id = row["id"]
                    for item in seed_exercises:
                        prompt, passage, answer, audio, mode = item[:5]
                        self.conn.execute(
                            """UPDATE exercises SET source='builtin'
                            WHERE topic_id=? AND prompt=? AND passage=? AND answer=?
                                AND audio_file=? AND mode=?""",
                            (topic_id, prompt, passage, answer, audio, mode),
                        )

            self.conn.execute("""
                UPDATE topics SET source='pdf'
                WHERE id IN (SELECT topic_id FROM pdf_imported_topics)
                    AND source='admin'
            """)
            self.conn.execute("""
                UPDATE exercises SET source='pdf'
                WHERE id IN (SELECT exercise_id FROM pdf_imported_exercises)
            """)
        self.conn.commit()

    def get_setting(self, key, default=""):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        self.conn.commit()

    def seed(self):
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version >= SEED_VERSION:
            return
        for category, topics in SEED.items():
            for name, desc, exercises in topics:
                if self.topic_exists(category, name):
                    continue
                tid = self.add_topic(category, name, desc, source="builtin")
                for item in exercises:
                    prompt, passage, answer, audio, mode = item[:5]
                    image = item[5] if len(item) > 5 else ""
                    self.add_exercise(
                        tid, prompt, passage, answer, audio, mode, image,
                        source="builtin",
                    )
        self.conn.execute("PRAGMA user_version = %d" % SEED_VERSION)
        self.conn.commit()

    def topics(self, category):
        return self.conn.execute(
            "SELECT * FROM topics WHERE category=? ORDER BY name", (category,)).fetchall()

    def exercises(self, topic_id):
        return self.conn.execute(
            "SELECT * FROM exercises WHERE topic_id=? ORDER BY id", (topic_id,)).fetchall()

    def exam_exercises(self, unit_filter="Todas", limit=EXAM_QUESTION_COUNT):
        if unit_filter.startswith("Unit"):
            selected_rows = self.conn.execute("""
                SELECT e.*, t.category, t.name AS topic_name
                FROM exercises e JOIN topics t ON t.id = e.topic_id
                WHERE t.name LIKE ?""", (unit_filter + "%",)).fetchall()
            items = [dict(r) for r in selected_rows]
            random.shuffle(items)
            if len(items) < limit:
                other_rows = self.conn.execute("""
                    SELECT e.*, t.category, t.name AS topic_name
                    FROM exercises e JOIN topics t ON t.id = e.topic_id
                    WHERE t.name NOT LIKE ?""", (unit_filter + "%",)).fetchall()
                other_items = [dict(r) for r in other_rows]
                random.shuffle(other_items)
                items.extend(other_items[:limit - len(items)])
        else:
            rows = self.conn.execute("""
                SELECT e.*, t.category, t.name AS topic_name
                FROM exercises e JOIN topics t ON t.id = e.topic_id""").fetchall()
            items = [dict(r) for r in rows]
            random.shuffle(items)
        return items[:limit]

    def add_topic(self, category, name, description="", source="admin"):
        cur = self.conn.execute(
            "INSERT INTO topics(category,name,description,source) VALUES(?,?,?,?)",
            (category, name, description, source))
        self.conn.commit()
        return cur.lastrowid

    def topic_exists(self, category, name):
        return self.conn.execute(
            "SELECT 1 FROM topics WHERE category=? AND lower(name)=lower(?)",
            (category, name)).fetchone() is not None

    def add_exercise(self, topic_id, prompt, passage, answer, audio="", mode="exact",
                     image="", source="admin"):
        cursor = self.conn.execute(
            "INSERT INTO exercises(topic_id,prompt,passage,answer,audio_file,mode,image_file,source) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (topic_id, prompt, passage, answer, audio, mode, image, source))
        self.conn.commit()
        return cursor.lastrowid

    def exercise(self, exercise_id):
        return self.conn.execute(
            "SELECT * FROM exercises WHERE id=?", (exercise_id,)).fetchone()

    def update_exercise(self, exercise_id, prompt, passage, answer, mode):
        cursor = self.conn.execute(
            "UPDATE exercises SET prompt=?,passage=?,answer=?,mode=?,source='admin' WHERE id=?",
            (prompt, passage, answer, mode, exercise_id),
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_exercise(self, exercise_id, user_id=None):
        with self._progress_lock:
            row = self.conn.execute(
                "SELECT 1 FROM exercises WHERE id=?", (exercise_id,)
            ).fetchone()
            if row is None:
                return False
            with self.conn:
                if user_id:
                    exercise_key = self.exercise_key(exercise_id)
                    deleted_before = int(time.time() * 1000)
                    self.conn.execute(
                        """INSERT INTO progress_deletions(
                            user_id,exercise_key,deleted_before
                        ) VALUES(?,?,?)
                        ON CONFLICT(user_id,exercise_key) DO UPDATE SET
                            deleted_before=excluded.deleted_before""",
                        (user_id, exercise_key, deleted_before),
                    )
                    self.conn.execute(
                        """DELETE FROM progress_events
                        WHERE user_id=? AND exercise_key=? AND created_at<=?""",
                        (user_id, exercise_key, deleted_before),
                    )
                cursor = self.conn.execute(
                    "DELETE FROM exercises WHERE id=?", (exercise_id,)
                )
        return cursor.rowcount > 0

    def replace_pdf_import(self, source_hash, topics):
        created_topics = 0
        created_exercises = 0
        with self.conn:
            self.conn.execute(
                """DELETE FROM exercises
                WHERE id IN (
                    SELECT exercise_id FROM pdf_imported_exercises WHERE source_hash=?
                )""",
                (source_hash,),
            )
            self.conn.execute(
                """DELETE FROM topics
                WHERE id IN (
                    SELECT topic_id FROM pdf_imported_topics WHERE source_hash=?
                )
                AND NOT EXISTS (
                    SELECT 1 FROM exercises WHERE exercises.topic_id=topics.id
                )""",
                (source_hash,),
            )

            for topic in topics:
                row = self.conn.execute(
                    "SELECT id FROM topics WHERE category=? AND lower(name)=lower(?)",
                    (topic["category"], topic["name"]),
                ).fetchone()
                if row:
                    topic_id = row["id"]
                else:
                    cursor = self.conn.execute(
                        "INSERT INTO topics(category,name,description,source) "
                        "VALUES(?,?,?,'pdf')",
                        (topic["category"], topic["name"], topic["description"]),
                    )
                    topic_id = cursor.lastrowid
                    self.conn.execute(
                        "INSERT INTO pdf_imported_topics(source_hash,topic_id) VALUES(?,?)",
                        (source_hash, topic_id),
                    )
                    created_topics += 1

                for exercise in topic["exercises"]:
                    cursor = self.conn.execute(
                        """INSERT INTO exercises(
                            topic_id,prompt,passage,answer,audio_file,mode,image_file,source
                        ) VALUES(?,?,?,?,?,?,?,'pdf')""",
                        (
                            topic_id,
                            exercise["prompt"],
                            exercise["passage"],
                            exercise["answer"],
                            "",
                            exercise["mode"],
                            exercise["image_file"],
                        ),
                    )
                    self.conn.execute(
                        "INSERT INTO pdf_imported_exercises(source_hash,exercise_id) VALUES(?,?)",
                        (source_hash, cursor.lastrowid),
                    )
                    created_exercises += 1

        return created_topics, created_exercises

    def shared_content_snapshot(self):
        topics = self.conn.execute("""
            SELECT DISTINCT t.id, t.category, t.name, t.description
            FROM topics t
            LEFT JOIN exercises e ON e.topic_id=t.id
            WHERE t.source IN ('admin','pdf')
                OR e.source IN ('admin','pdf')
            ORDER BY t.category, t.name
        """).fetchall()
        snapshot_topics = []
        for topic in topics:
            exercises = self.conn.execute("""
                SELECT prompt, passage, answer, mode, image_file
                FROM exercises
                WHERE topic_id=? AND source IN ('admin','pdf')
                ORDER BY id
            """, (topic["id"],)).fetchall()
            snapshot_topics.append({
                "category": topic["category"],
                "name": topic["name"],
                "description": topic["description"] or "",
                "exercises": [dict(exercise) for exercise in exercises],
            })
        return {"version": 1, "topics": snapshot_topics}

    def replace_shared_content(self, topics):
        if not isinstance(topics, list):
            raise ValueError("La biblioteca compartida no contiene una lista de temas.")
        for topic in topics:
            if (not isinstance(topic, dict)
                    or topic.get("category") not in CATEGORIES
                    or not isinstance(topic.get("name"), str)
                    or not topic["name"].strip()
                    or not isinstance(topic.get("description", ""), str)
                    or not isinstance(topic.get("exercises"), list)):
                raise ValueError("Firebase devolvió un tema compartido no válido.")
            for exercise in topic["exercises"]:
                if (not isinstance(exercise, dict)
                        or not isinstance(exercise.get("prompt"), str)
                        or not exercise["prompt"].strip()
                        or not isinstance(exercise.get("passage", ""), str)
                        or not isinstance(exercise.get("answer"), str)
                        or not exercise["answer"].strip()
                        or not isinstance(exercise.get("mode", "exact"), str)
                        or not isinstance(exercise.get("image_file", ""), str)):
                    raise ValueError(
                        "Firebase devolvió un ejercicio compartido no válido."
                    )

        with self._progress_lock, self.conn:
            self.conn.execute("DELETE FROM exercises WHERE source='shared'")
            self.conn.execute("""
                DELETE FROM topics
                WHERE source='shared'
                    AND NOT EXISTS (
                        SELECT 1 FROM exercises WHERE exercises.topic_id=topics.id
                    )
            """)
            for topic in topics:
                row = self.conn.execute(
                    """SELECT id, source FROM topics
                    WHERE category=? AND lower(name)=lower(?) LIMIT 1""",
                    (topic["category"], topic["name"].strip()),
                ).fetchone()
                if row is None:
                    cursor = self.conn.execute(
                        """INSERT INTO topics(category,name,description,source)
                        VALUES(?,?,?,'shared')""",
                        (
                            topic["category"], topic["name"].strip(),
                            topic.get("description", ""),
                        ),
                    )
                    topic_id = cursor.lastrowid
                else:
                    topic_id = row["id"]
                    if row["source"] == "shared":
                        self.conn.execute(
                            "UPDATE topics SET description=? WHERE id=?",
                            (topic.get("description", ""), topic_id),
                        )
                for exercise in topic["exercises"]:
                    self.conn.execute(
                        """INSERT INTO exercises(
                            topic_id,prompt,passage,answer,audio_file,mode,image_file,source
                        ) VALUES(?,?,?,?,?,?,?,'shared')""",
                        (
                            topic_id, exercise["prompt"].strip(),
                            exercise.get("passage", ""), exercise["answer"].strip(),
                            "", exercise.get("mode", "exact"),
                            exercise.get("image_file", ""),
                        ),
                    )

    def delete_topic(self, topic_id, user_id=None):
        with self._progress_lock:
            exercise_rows = self.conn.execute(
                "SELECT id FROM exercises WHERE topic_id=?", (topic_id,)
            ).fetchall()
            with self.conn:
                if user_id:
                    deleted_before = int(time.time() * 1000)
                    for exercise in exercise_rows:
                        exercise_key = self.exercise_key(exercise["id"])
                        self.conn.execute(
                            """INSERT INTO progress_deletions(
                                user_id,exercise_key,deleted_before
                            ) VALUES(?,?,?)
                            ON CONFLICT(user_id,exercise_key) DO UPDATE SET
                                deleted_before=excluded.deleted_before""",
                            (user_id, exercise_key, deleted_before),
                        )
                        self.conn.execute(
                            """DELETE FROM progress_events
                            WHERE user_id=? AND exercise_key=? AND created_at<=?""",
                            (user_id, exercise_key, deleted_before),
                        )
                self.conn.execute("DELETE FROM topics WHERE id=?", (topic_id,))

    def exercise_key(self, exercise_id):
        row = self.conn.execute("""
            SELECT t.category, t.name, e.prompt, e.answer
            FROM exercises e
            JOIN topics t ON t.id = e.topic_id
            WHERE e.id=?""", (exercise_id,)).fetchone()
        if row is None:
            raise KeyError("El ejercicio no existe.")
        return self._exercise_key_from_values(
            row["category"], row["name"], row["prompt"], row["answer"]
        )

    @staticmethod
    def _exercise_key_from_values(category, name, prompt, answer):
        values = [str(value or "").strip().casefold()
                  for value in (category, name, prompt, answer)]
        return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()

    def record_attempt(self, exercise_id, correct, user_id=None):
        if not user_id:
            with self._progress_lock:
                self.conn.execute(
                    "INSERT INTO attempts(exercise_id,correct) VALUES(?,?)",
                    (exercise_id, 1 if correct else 0),
                )
                self.conn.commit()
            return None

        with self._progress_lock:
            row = self.conn.execute("""
                SELECT t.category
                FROM exercises e JOIN topics t ON t.id=e.topic_id
                WHERE e.id=?""", (exercise_id,)).fetchone()
            if row is None:
                raise KeyError("El ejercicio no existe.")
            event_id = uuid.uuid4().hex
            created_at = int(time.time() * 1000)
            event = {
                "category": row["category"],
                "correct": bool(correct),
                "created_at": created_at,
                "exercise_key": self.exercise_key(exercise_id),
            }
            with self.conn:
                self.conn.execute(
                    """INSERT INTO progress_events(
                        user_id,event_id,category,correct,exercise_key,created_at,synced
                    ) VALUES(?,?,?,?,?,?,0)""",
                    (
                        user_id, event_id, event["category"], int(bool(correct)),
                        event["exercise_key"], created_at,
                    ),
                )
        return event_id, event

    def merge_remote_progress(self, user_id, events):
        with self._progress_lock:
            with self.conn:
                for event_id, event in events.items():
                    if not isinstance(event, dict):
                        raise ValueError("Firebase devolvió un evento de progreso no válido.")
                    category = event.get("category")
                    correct = event.get("correct")
                    exercise_key = event.get("exercise_key")
                    created_at = event.get("created_at")
                    if (category not in CATEGORIES or not isinstance(correct, bool)
                            or not isinstance(exercise_key, str)
                            or not isinstance(created_at, (int, float))):
                        raise ValueError(
                            "Firebase devolvió un evento de progreso incompleto."
                        )
                    self.conn.execute(
                        """INSERT OR IGNORE INTO progress_events(
                            user_id,event_id,category,correct,exercise_key,created_at,synced
                        ) VALUES(?,?,?,?,?,?,1)""",
                        (
                            user_id, event_id, category, int(correct), exercise_key,
                            int(created_at),
                        ),
                    )

    def pending_progress(self, user_id):
        with self._progress_lock:
            rows = self.conn.execute("""
                SELECT event_id, category, correct, exercise_key, created_at
                FROM progress_events
                WHERE user_id=? AND synced=0
                ORDER BY created_at, event_id""", (user_id,)).fetchall()
        return [
            (
                row["event_id"],
                {
                    "category": row["category"],
                    "correct": bool(row["correct"]),
                    "created_at": row["created_at"],
                    "exercise_key": row["exercise_key"],
                },
            )
            for row in rows
        ]

    def pending_progress_deletions(self, user_id):
        with self._progress_lock:
            rows = self.conn.execute(
                """SELECT exercise_key, deleted_before FROM progress_deletions
                WHERE user_id=? ORDER BY deleted_before""",
                (user_id,),
            ).fetchall()
        return {
            row["exercise_key"]: row["deleted_before"] for row in rows
        }

    def mark_progress_deletions_synced(self, user_id, exercise_keys):
        with self._progress_lock:
            with self.conn:
                self.conn.executemany(
                    """DELETE FROM progress_deletions
                    WHERE user_id=? AND exercise_key=?""",
                    [(user_id, key) for key in exercise_keys],
                )

    def mark_progress_synced(self, user_id, event_id):
        with self._progress_lock:
            with self.conn:
                self.conn.execute(
                    "UPDATE progress_events SET synced=1 WHERE user_id=? AND event_id=?",
                    (user_id, event_id),
                )

    def stats(self, user_id=None):
        if not user_id:
            return {}
        with self._progress_lock:
            rows = self.conn.execute("""
                SELECT category, COUNT(*) AS total, COALESCE(SUM(correct), 0) AS good
                FROM progress_events
                WHERE user_id=?
                GROUP BY category""", (user_id,)).fetchall()
        return {r["category"]: (r["total"], r["good"]) for r in rows}

    def reset_progress(self, user_id):
        if not user_id:
            raise ValueError("Se necesita una cuenta para borrar el progreso.")
        with self._progress_lock:
            with self.conn:
                self.conn.execute(
                    "DELETE FROM progress_events WHERE user_id=?", (user_id,)
                )
                self.conn.execute(
                    "DELETE FROM progress_deletions WHERE user_id=?", (user_id,)
                )


def resolve_image_path(img_name):
    """Busca primero en imágenes recortadas por IA y luego en assets/images/."""
    if not img_name:
        return ""
    user_img = os.path.join(App.get_running_app().user_images_dir, img_name)
    if os.path.exists(user_img):
        return user_img
    bundled_img = os.path.join(BUNDLED_IMAGE_DIR, img_name)
    if os.path.exists(bundled_img):
        return bundled_img
    return ""


def confirm(title, message, on_yes):
    box = BoxLayout(orientation="vertical", spacing=dp(14), padding=dp(16))
    lbl = Label(text=message, halign="center", valign="middle", color=TEXT)
    lbl.bind(size=lambda w, s: setattr(w, "text_size", (s[0], s[1])))
    box.add_widget(lbl)
    row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
    popup = Popup(title=title, content=box, size_hint=(0.88, None), height=dp(220),
                  background="", background_color=SURFACE, separator_color=PRIMARY,
                  title_color=TEXT)
    yes = RBtn(text="Yes", bg=[0.86, 0.27, 0.27, 1], height=dp(48))
    no = RBtn(text="Cancel", bg=list(SURFACE2), height=dp(48))
    yes.bind(on_release=lambda *_: (popup.dismiss(), on_yes()))
    no.bind(on_release=popup.dismiss)
    row.add_widget(yes)
    row.add_widget(no)
    box.add_widget(row)
    popup.open()


# --------------------------------------------------------------------------
# Voz (TTS y Micrófono nativo Android) + Selector nativo de PDF Android
# --------------------------------------------------------------------------
def spoken_text(category, passage):
    text = passage or ""
    if category == "Speaking" and ":" in text:
        head, tail = text.split(":", 1)
        if head.strip().lower() in ("modelo", "model"):
            text = tail
    text = re.sub(r"(?:(?<=\s)|^)[AB]:\s*", "\n", text)
    text = text.replace("...", ", ")
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


class Speaker:
    def __init__(self):
        self.error = ""
        self._engine = None
        self._ready = False
        self._proc = None
        if platform == "android":
            self._init_android()

    def _init_android(self):
        self._status = None
        try:
            from jnius import autoclass, PythonJavaClass, java_method  # type: ignore[reportMissingImports]

            class InitListener(PythonJavaClass):
                __javainterfaces__ = ["android/speech/tts/TextToSpeech$OnInitListener"]
                __javacontext__ = "app"

                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback

                @java_method("(I)V")
                def onInit(self, status):
                    self.callback(status)

            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            self._tts_cls = autoclass("android.speech.tts.TextToSpeech")
            self._locale = autoclass("java.util.Locale")
            self._listener = InitListener(self._on_init)
            self._engine = self._tts_cls(activity, self._listener)
        except Exception as e:
            self._engine = None
            self.error = "No se pudo iniciar la voz: %s" % e

    def _on_init(self, status):
        self._status = status

    def _finish_init(self):
        if self._ready or self._status is None or self._engine is None:
            return
        if self._status == self._tts_cls.SUCCESS:
            self._engine.setLanguage(self._locale.US)
            self._ready = True

    def speak(self, lines, slow=False):
        self.stop()
        if not lines:
            return "Sin texto para leer."
        if platform != "android":
            return self._speak_desktop(lines, slow)
        if not self._ready:
            self._finish_init()
        if not self._ready or self._engine is None:
            return "Iniciando voz, intenta de nuevo en un segundo."
        self._engine.setSpeechRate(0.6 if slow else 0.95)
        for i, line in enumerate(lines):
            mode = self._tts_cls.QUEUE_FLUSH if i == 0 else self._tts_cls.QUEUE_ADD
            try:
                self._engine.speak(line, mode, None, None)
            except Exception:
                self._engine.speak(line, mode, None)
        return ""

    def _speak_desktop(self, lines, slow):
        import subprocess
        text = ". ".join(lines)
        if platform == "win":
            script = ("Add-Type -AssemblyName System.Speech;"
                      "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                      "$s.Rate = %d; $s.Speak($env:QUIZ_TEXT)" % (-3 if slow else 0))
            try:
                self._proc = subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", script],
                    env=dict(os.environ, QUIZ_TEXT=text), creationflags=0x08000000)
            except Exception:
                return "Voz no disponible en este equipo."
        return ""

    def stop(self):
        if self._engine and self._ready:
            try:
                self._engine.stop()
            except Exception:
                pass
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def shutdown(self):
        self.stop()
        if self._engine:
            try:
                self._engine.shutdown()
            except Exception:
                pass


class VoiceRecognizer:
    def listen(self, on_result, on_error):
        if platform != "android":
            on_error("El micrófono funciona en Android. En PC escribe el mensaje.")
            return
        try:
            from android.permissions import request_permissions, Permission  # type: ignore[reportMissingImports]
            from jnius import autoclass, PythonJavaClass, java_method  # type: ignore[reportMissingImports]
            from android.runnable import run_on_ui_thread  # type: ignore[reportMissingImports]

            request_permissions([Permission.RECORD_AUDIO])

            SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")
            RecognizerIntent = autoclass("android.speech.RecognizerIntent")
            Intent = autoclass("android.content.Intent")
            activity = autoclass("org.kivy.android.PythonActivity").mActivity

            class Listener(PythonJavaClass):
                __javainterfaces__ = ["android/speech/RecognitionListener"]
                __javacontext__ = "app"

                @java_method("(Landroid/os/Bundle;)V")
                def onResults(self, results):
                    matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    if matches and matches.size() > 0:
                        text = matches.get(0)
                        Clock.schedule_once(lambda *_: on_result(text), 0)

                @java_method("(I)V")
                def onError(self, error):
                    Clock.schedule_once(lambda *_: on_error("No se escuchó audio (código %d)." % error), 0)

                @java_method("(Landroid/os/Bundle;)V")
                def onReadyForSpeech(self, params): pass

                @java_method("()V")
                def onBeginningOfSpeech(self): pass

                @java_method("(F)V")
                def onRmsChanged(self, rmsdB): pass

                @java_method("([B)V")
                def onBufferReceived(self, buffer): pass

                @java_method("()V")
                def onEndOfSpeech(self): pass

                @java_method("(Landroid/os/Bundle;)V")
                def onPartialResults(self, partialResults): pass

                @java_method("(ILandroid/os/Bundle;)V")
                def onEvent(self, eventType, params): pass

            @run_on_ui_thread
            def _start():
                self._sr = SpeechRecognizer.createSpeechRecognizer(activity)
                self._listener = Listener()
                self._sr.setRecognitionListener(self._listener)
                intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-US")
                self._sr.startListening(intent)

            _start()
        except Exception as e:
            on_error("Error de micrófono: %s" % e)


def pick_pdf_file(temp_dir, on_picked, on_error):
    """Abre el selector de archivos de la plataforma actual."""
    if platform != "android":
        try:
            import tkinter as tk
            from tkinter import filedialog
        except ImportError as exc:
            on_error("No está disponible el selector de archivos: %s" % exc)
            return

        root = None
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            pdf_path = filedialog.askopenfilename(
                parent=root,
                title="Selecciona un libro PDF",
                filetypes=[("Archivos PDF", "*.pdf")],
            )
        except tk.TclError as exc:
            on_error("No se pudo abrir el selector de PDF: %s" % exc)
            return
        finally:
            if root is not None:
                root.destroy()

        if pdf_path:
            on_picked(pdf_path)
        else:
            on_error("Selección de PDF cancelada.")
        return

    try:
        from android import activity as android_activity  # type: ignore[reportMissingImports]
        from jnius import autoclass  # type: ignore[reportMissingImports]

        Intent = autoclass("android.content.Intent")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        current_activity = PythonActivity.mActivity
        REQ_CODE = 7412

        def _on_activity_result(request_code, result_code, data):
            if request_code != REQ_CODE:
                return
            android_activity.unbind(on_activity_result=_on_activity_result)
            if result_code != -1 or data is None:
                Clock.schedule_once(lambda *_: on_error("Selección de PDF cancelada."), 0)
                return
            try:
                uri = data.getData()
                resolver = current_activity.getContentResolver()
                inp = resolver.openInputStream(uri)
                dest = os.path.join(temp_dir, "imported_book.pdf")
                with open(dest, "wb") as out_f:
                    buf = bytearray(8192)
                    while True:
                        n = inp.read(buf)
                        if n <= 0:
                            break
                        out_f.write(buf[:n])
                inp.close()
                Clock.schedule_once(lambda *_: on_picked(dest), 0)
            except Exception as exc:
                Clock.schedule_once(lambda *_: on_error("No se pudo leer el PDF: %s" % exc), 0)

        android_activity.bind(on_activity_result=_on_activity_result)
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("application/pdf")
        current_activity.startActivityForResult(intent, REQ_CODE)
    except Exception as e:
        on_error("Error abriendo selector de archivos: %s" % e)


# --------------------------------------------------------------------------
# Pantallas
# --------------------------------------------------------------------------
class LoginScreen(Screen):
    def on_pre_enter(self, *args):
        app = App.get_running_app()
        if not app.firebase.api_key:
            self.ids.status.text = "Configura FIREBASE_WEB_API_KEY en main.py."
            self.ids.status.color = BAD_COLOR
        elif not app.firebase.database_url.startswith("https://"):
            self.ids.status.text = "Configura la URL de Firebase."
            self.ids.status.color = BAD_COLOR

    def login(self):
        email = self.ids.email.text.strip()
        password = self.ids.password.text
        if not email or not password:
            self.ids.status.text = "Escribe tu correo y contraseña."
            self.ids.status.color = BAD_COLOR
            return
        self.ids.login_button.disabled = True
        self.ids.status.text = "Conectando con Firebase..."
        self.ids.status.color = INFO_COLOR
        App.get_running_app().authenticate(
            email, password, register=False, screen_name="login"
        )

    def open_registration(self):
        self.manager.transition.direction = "left"
        self.manager.current = "register"


class RegisterScreen(Screen):
    def register(self):
        email = self.ids.email.text.strip()
        password = self.ids.password.text
        confirmation = self.ids.confirm_password.text
        if not email or not password:
            self.ids.status.text = "Escribe tu correo y contraseña."
            self.ids.status.color = BAD_COLOR
            return
        if password != confirmation:
            self.ids.status.text = "Las contraseñas no coinciden."
            self.ids.status.color = BAD_COLOR
            return
        self.ids.register_button.disabled = True
        self.ids.status.text = "Creando cuenta de usuario..."
        self.ids.status.color = INFO_COLOR
        App.get_running_app().authenticate(
            email, password, register=True, screen_name="register"
        )

    def go_login(self):
        self.manager.transition.direction = "right"
        self.manager.current = "login"


class HomeScreen(Screen):
    def on_pre_enter(self, *args):
        app = App.get_running_app()
        user = app.current_user
        if user is None:
            self.manager.current = "login"
            return
        data = app.db.stats(user["uid"])
        total = sum(t for t, _ in data.values())
        good = sum(g for _, g in data.values())
        pct = int(round(100.0 * good / total)) if total else 0
        self.ids.home_pct.text = "%d%%" % pct
        self.ids.home_detail.text = (
            "%d de %d respuestas correctas" % (good, total) if total
            else "Aún sin resultados. ¡Empieza en Práctica o Evaluación!")
        self.ids.home_bar.maximum = 100
        Animation(value=pct, d=0.4, t="out_quad").start(self.ids.home_bar)
        role_name = "Administrador" if app.is_admin else "Usuario"
        self.ids.signed_in_user.text = "%s • %s" % (user["email"], role_name)
        self.ids.home_sync_status.text = app.sync_status

    def go(self, name):
        if name == "admin" and not App.get_running_app().is_admin:
            return
        self.manager.transition.direction = "left"
        self.manager.current = name


class PracticeHubScreen(Screen):
    def on_pre_enter(self, *args):
        is_admin = App.get_running_app().is_admin
        button = self.ids.manage_pdf_button
        grid = self.ids.practice_grid
        if is_admin:
            if button.parent is None:
                grid.add_widget(button)
        elif button.parent is not None:
            grid.remove_widget(button)
        button.opacity = 1 if is_admin else 0
        button.disabled = not is_admin

    def open_area(self, category):
        self.manager.get_screen("area").set_category(category)
        self.go("area")

    def open_admin(self):
        if not App.get_running_app().is_admin:
            return
        self.go("admin")

    def go(self, name):
        if name == "admin" and not App.get_running_app().is_admin:
            return
        self.manager.transition.direction = "left"
        self.manager.current = name

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"


class AreaScreen(Screen):
    category = ""
    exercises = []
    topic_map = {}
    index = 0
    first_try = True
    correct_count = 0
    sound = None

    def set_category(self, category):
        self.category = category
        ids = self.ids
        can_delete = App.get_running_app().is_admin
        ids.delete_exercise_button.height = dp(48) if can_delete else 0
        ids.delete_exercise_button.opacity = 1 if can_delete else 0
        ids.delete_exercise_button.disabled = not can_delete
        ids.area_title.text = category
        ids.instruction.text = DESCRIPTIONS.get(category, "")
        rows = App.get_running_app().db.topics(category)
        self.topic_map = {r["name"]: r["id"] for r in rows}
        self.exercises = []
        self.index = 0
        self.correct_count = 0
        self.correct_exercise_ids = set()
        self.reset_display()
        show_audio = category in ("Listening", "Speaking")
        ids.audio_button.text = "Play audio" if category == "Listening" else "Listen to the model"
        ids.audio_row.disabled = not show_audio
        ids.audio_row.opacity = 1 if show_audio else 0
        ids.audio_row.height = dp(50) if show_audio else 0
        accent = list(AREA_COLORS.get(category, PRIMARY))
        ids.bar.fill = accent
        ids.check_btn.bg = accent
        ids.topic_spinner.values = list(self.topic_map)
        ids.topic_spinner.text = "Select a topic"
        if self.topic_map:
            ids.topic_spinner.text = next(iter(self.topic_map))

    def reset_display(self):
        ids = self.ids
        ids.prompt.text = "Elige un tema para empezar."
        ids.passage.text = ""
        ids.answer.text = ""
        ids.ex_image.source = ""
        ids.ex_image.opacity = 0
        ids.ex_image.height = 0
        self.clear_feedback()
        ids.progress.text = ""
        ids.bar.value = 0

    def load_topic(self, name):
        if name not in self.topic_map:
            return
        self.stop_audio()
        self.exercises = App.get_running_app().db.exercises(self.topic_map[name])
        self.index = 0
        self.correct_count = 0
        self.correct_exercise_ids = set()
        self.show_exercise()

    @property
    def current(self):
        return self.exercises[self.index] if self.exercises else None

    def show_exercise(self):
        ids = self.ids
        item = self.current
        if item is None:
            ids.prompt.text = "Este tema aún no tiene ejercicios."
            return
        self.first_try = True
        ids.prompt.text = item["prompt"]
        ids.passage.text = "" if self.category == "Listening" else item["passage"]
        ids.answer.text = ""
        self.clear_feedback()

        img_name = item["image_file"] if "image_file" in item.keys() else ""
        img_path = resolve_image_path(img_name)
        if img_path:
            ids.ex_image.source = img_path
            ids.ex_image.opacity = 1
            ids.ex_image.height = dp(170)
        else:
            ids.ex_image.source = ""
            ids.ex_image.opacity = 0
            ids.ex_image.height = 0

        total = len(self.exercises)
        ids.progress.text = "Ejercicio %d de %d  •  Aciertos: %d" % (
            self.index + 1, total, self.correct_count)
        ids.bar.maximum = total
        Animation(value=self.index + 1, d=0.3, t="out_quad").start(ids.bar)

    def check_answer(self):
        item = self.current
        if item is None:
            return
        given = self.ids.answer.text
        if not given.strip():
            self.set_feedback("Escribe una respuesta primero.", BAD_COLOR)
            return
        ok = is_correct(given, item["answer"], item["mode"] or "exact")
        if self.first_try:
            App.get_running_app().record_attempt(item["id"], ok)
            if ok:
                self.correct_count += 1
                self.correct_exercise_ids.add(item["id"])
                self.ids.progress.text = "Ejercicio %d de %d  •  Aciertos: %d" % (
                    self.index + 1, len(self.exercises), self.correct_count)
            self.first_try = False
        if ok:
            self.set_feedback("¡Muy bien! Respuesta correcta.", OK_COLOR)
        else:
            self.set_feedback("Inténtalo de nuevo o pulsa 'Show answer'.", BAD_COLOR)

    def show_answer(self):
        item = self.current
        if item is None:
            return
        if self.first_try:
            App.get_running_app().record_attempt(item["id"], False)
            self.first_try = False
        options = alternatives(item["answer"])
        self.set_feedback("Respuesta esperada: " + " / ".join(options), INFO_COLOR)

    def next_exercise(self):
        if not self.exercises:
            return
        self.stop_audio()
        if self.index + 1 >= len(self.exercises):
            self.set_feedback("¡Tema completado! Aciertos: %d de %d." % (
                self.correct_count, len(self.exercises)), OK_COLOR)
            self.index = 0
            self.correct_count = 0
            self.correct_exercise_ids = set()
            return
        self.index += 1
        self.show_exercise()

    def confirm_delete_current_exercise(self):
        if not App.get_running_app().is_admin:
            return
        item = self.current
        if item is None:
            self.set_feedback("Elige un tema con ejercicios primero.", BAD_COLOR)
            return
        confirm(
            "Eliminar ejercicio",
            "¿Eliminar este ejercicio y su progreso?\n\n%s" % item["prompt"],
            lambda: self.delete_current_exercise(item["id"]),
        )

    def delete_current_exercise(self, exercise_id):
        if not App.get_running_app().is_admin:
            return
        app = App.get_running_app()
        db = app.db
        self.stop_audio()
        if not db.delete_exercise(
            exercise_id, user_id=app.current_user["uid"]
        ):
            self.load_topic(self.ids.topic_spinner.text)
            self.set_feedback("El ejercicio ya no existe. Actualicé la lista.", BAD_COLOR)
            return
        app._sync_progress_async(fetch_remote=False)
        app._publish_shared_content_async(
            lambda error: app.root.get_screen("admin").say(
                error or "Ejercicio eliminado de la biblioteca compartida.",
                error is None,
            )
        )

        if exercise_id in self.correct_exercise_ids:
            self.correct_exercise_ids.remove(exercise_id)
            self.correct_count -= 1
        self.exercises = [
            item for item in self.exercises if item["id"] != exercise_id
        ]
        if not self.exercises:
            self.index = 0
            self.reset_display()
            self.ids.prompt.text = "Este tema aún no tiene ejercicios."
            self.set_feedback("Ejercicio eliminado. No quedan ejercicios en este tema.",
                              INFO_COLOR)
            return

        self.index = min(self.index, len(self.exercises) - 1)
        self.show_exercise()
        self.set_feedback("Ejercicio eliminado.", INFO_COLOR)

    def set_feedback(self, text, color):
        fb = self.ids.feedback
        fb.text = text
        fb.color = color
        fb.bg = (color[0], color[1], color[2], 0.16)

    def clear_feedback(self):
        fb = self.ids.feedback
        fb.text = ""
        fb.bg = (0, 0, 0, 0)

    def stop_audio(self):
        App.get_running_app().speaker.stop()
        if self.sound:
            try:
                self.sound.stop()
            except Exception:
                pass
            self.sound = None

    def play_audio(self, slow=False):
        item = self.current
        if item is None:
            return
        self.stop_audio()
        name = item["audio_file"]
        path = os.path.join(AUDIO_DIR, name) if name else ""
        if not slow and path and os.path.exists(path):
            self.sound = SoundLoader.load(path)
            if self.sound:
                self.sound.play()
                return
        lines = spoken_text(self.category, item["passage"])
        message = App.get_running_app().speaker.speak(lines, slow)
        if message:
            self.set_feedback(message, BAD_COLOR)

    def go_back(self):
        self.stop_audio()
        self.manager.transition.direction = "right"
        self.manager.current = "practice_hub"

    def on_leave(self, *args):
        self.stop_audio()


# --------------------------------------------------------------------------
# Pantalla de Evaluación (Quiz sin ayudas ni pistas)
# --------------------------------------------------------------------------
class ExamScreen(Screen):
    questions = []
    index = 0
    results = []

    def start_exam(self):
        unit = self.ids.unit_spinner.text
        self.questions = App.get_running_app().db.exam_exercises(
            unit, limit=EXAM_QUESTION_COUNT)
        self.index = 0
        self.results = []
        ids = self.ids
        ids.exam_result.text = ""
        ids.exam_result.bg = (0, 0, 0, 0)
        if not self.questions:
            ids.exam_prompt.text = "No hay preguntas disponibles para esta unidad."
            return
        ids.exam_answer.disabled = False
        ids.exam_submit_btn.disabled = False
        self.show_question()

    def show_question(self):
        ids = self.ids
        q = self.questions[self.index]
        total = len(self.questions)
        ids.exam_cat.text = "%s  •  %s" % (q["category"].upper(), q["topic_name"])
        ids.exam_prompt.text = q["prompt"]
        ids.exam_passage.text = q["passage"] if q["category"] == "Reading" else ""

        img_path = resolve_image_path(q.get("image_file", ""))
        if img_path:
            ids.exam_image.source = img_path
            ids.exam_image.opacity = 1
            ids.exam_image.height = dp(160)
        else:
            ids.exam_image.source = ""
            ids.exam_image.opacity = 0
            ids.exam_image.height = 0

        is_listening = q["category"] == "Listening"
        ids.exam_audio_btn.disabled = not is_listening
        ids.exam_audio_btn.opacity = 1 if is_listening else 0
        ids.exam_audio_btn.height = dp(48) if is_listening else 0

        ids.exam_answer.text = ""
        ids.exam_progress.text = "Pregunta %d de %d (Sin ayudas)" % (self.index + 1, total)
        ids.exam_bar.maximum = total
        Animation(value=self.index + 1, d=0.25, t="out_quad").start(ids.exam_bar)
        ids.exam_submit_btn.text = "Finalizar Examen" if self.index + 1 == total else "Siguiente pregunta  >"

    def play_exam_audio(self):
        if not self.questions:
            return
        q = self.questions[self.index]
        lines = spoken_text(q["category"], q["passage"])
        App.get_running_app().speaker.speak(lines, False)

    def submit_and_next(self):
        if not self.questions:
            return
        App.get_running_app().speaker.stop()
        q = self.questions[self.index]
        given = self.ids.exam_answer.text.strip()
        ok = is_correct(given, q["answer"], q["mode"] or "exact")
        App.get_running_app().record_attempt(q["id"], ok)
        self.results.append((q, given, ok))

        if self.index + 1 < len(self.questions):
            self.index += 1
            self.show_question()
        else:
            self.finish_exam()

    def finish_exam(self):
        ids = self.ids
        ids.exam_answer.disabled = True
        ids.exam_submit_btn.disabled = True
        ids.exam_audio_btn.disabled = True
        ids.exam_audio_btn.opacity = 0
        ids.exam_audio_btn.height = 0
        ids.exam_image.opacity = 0
        ids.exam_image.height = 0

        good = sum(1 for _, _, ok in self.results if ok)
        total = len(self.results)
        pct = int(round(100.0 * good / total)) if total else 0

        lines = ["CALIFICACIÓN FINAL: %d / %d (%d%%)\n" % (good, total, pct)]
        for i, (q, given, ok) in enumerate(self.results, 1):
            mark = "OK" if ok else "X"
            expected = alternatives(q["answer"])[0]
            if ok:
                lines.append("%d. [%s] %s -> %s" % (i, mark, q["prompt"], given))
            else:
                lines.append("%d. [%s] %s\n     Tu resp: %s | Correcta: %s" % (
                    i, mark, q["prompt"], given or "(vacío)", expected))

        color = OK_COLOR if pct >= 70 else BAD_COLOR
        ids.exam_result.text = "\n".join(lines)
        ids.exam_result.color = color
        ids.exam_result.bg = (color[0], color[1], color[2], 0.16)
        ids.exam_prompt.text = "Evaluación completada. Revisa tus resultados abajo."
        ids.exam_passage.text = ""
        ids.exam_progress.text = "Examen finalizado"

    def go_home(self):
        App.get_running_app().speaker.stop()
        self.manager.transition.direction = "right"
        self.manager.current = "home"


# --------------------------------------------------------------------------
# Pantalla de Conversación Online con Amigo
# --------------------------------------------------------------------------
class ChatScreen(Screen):
    guide_index = 0
    chat_client = None
    chat_recognizer = None

    def _show_status(self, message, color=INFO_COLOR):
        status = self.ids.mic_status
        status.text = message
        status.color = color
        status.bg = (color[0], color[1], color[2], 0.16)

    def next_topic_guide(self):
        self.guide_index = (self.guide_index + 1) % len(CONVERSATION_PROMPTS)
        self.ids.topic_guide.text = "Tema sugerido: " + CONVERSATION_PROMPTS[self.guide_index]

    def send_message(self):
        text = self.ids.chat_input.text.strip()
        if not text:
            self._show_status("Escribe un mensaje antes de enviarlo.", BAD_COLOR)
            return
        client = self._get_client()
        if not client.is_configured() or not client.room_code:
            self._show_status("Primero únete a una sala.", BAD_COLOR)
            return
        client.send_message(text)
        self.ids.chat_input.text = ""

    def start_voice_input(self):
        if self.chat_recognizer is None:
            self.chat_recognizer = VoiceRecognizer()
        self._show_status("Escuchando...", INFO_COLOR)
        self.chat_recognizer.listen(
            lambda text: Clock.schedule_once(
                lambda *_: self._voice_result(text), 0
            ),
            lambda error: Clock.schedule_once(
                lambda *_: self._show_status(error, BAD_COLOR), 0
            ),
        )

    def _voice_result(self, text):
        self.ids.chat_input.text = text
        self._show_status("Texto reconocido. Pulsa Enviar.", INFO_COLOR)

    def _get_client(self):
        app = App.get_running_app()
        db = app.db
        url = db.get_setting("firebase_db_url", FIREBASE_DB_URL)
        if self.chat_client is None or self.chat_client.base_url != url.strip().rstrip("/"):
            self.chat_client = OnlineChatClient(url, token_provider=app.get_id_token)
        return self.chat_client

    def on_pre_enter(self, *args):
        saved_name = App.get_running_app().db.get_setting("chat_user_name", "")
        if saved_name:
            self.ids.my_name.text = saved_name
        box = self.ids.chat_box
        if len(box.children) == 0:
            box.add_widget(ChatBubble(
                sender="Guía",
                msg="Escribe tu nombre y un código de sala (ej. JUAN-24) y pulsa Unirse.",
                bubble_bg=list(SURFACE)))

    def connect_friend(self):
        code = self.ids.friend_code.text.strip().upper()
        name = self.ids.my_name.text.strip() or "Estudiante"
        if not code:
            self._show_status("Escribe un código de invitación (ej. JUAN-24).", BAD_COLOR)
            return
        client = self._get_client()
        if not client.is_configured():
            self._show_status("Primero guarda tu URL de Firebase en Manage / PDF.", BAD_COLOR)
            return

        App.get_running_app().db.set_setting("chat_user_name", name)
        self._show_status("Conectando a la sala %s..." % code, INFO_COLOR)

        def on_msgs(messages):
            Clock.schedule_once(lambda *_: self._render_messages(messages, name), 0)

        def on_err(err):
            Clock.schedule_once(lambda *_: self._show_status(err, BAD_COLOR), 0)

        client.join_room(code, name, on_msgs, on_err)

    def _render_messages(self, messages, my_name):
        self.ids.mic_status.text = ""
        self.ids.mic_status.bg = (0, 0, 0, 0)
        box = self.ids.chat_box
        box.clear_widgets()
        for m in messages:
            sender = m.get("sender", "")
            is_me = sender.lower() == my_name.lower()
            box.add_widget(ChatBubble(
                sender="Tú" if is_me else sender,
                msg=m.get("message", ""),
                bubble_bg=[0.20, 0.47, 0.93, 1] if is_me else list(SURFACE)))

    def go_home(self):
        if self.chat_client is not None:
            self.chat_client.leave_room()
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_leave(self, *args):
        if self.chat_client is not None:
            self.chat_client.leave_room()


class StatsScreen(Screen):
    def on_pre_enter(self, *args):
        reset_button = self.ids.reset_progress_button
        is_admin = App.get_running_app().is_admin
        reset_button.height = dp(48) if is_admin else 0
        reset_button.opacity = 1 if is_admin else 0
        reset_button.disabled = not is_admin
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        if app.current_user is None:
            return
        data = app.db.stats(app.current_user["uid"])
        box = self.ids.stats_box
        box.clear_widgets()
        total_all = sum(total for total, _ in data.values())
        good_all = sum(good for _, good in data.values())
        pct_all = int(round(100.0 * good_all / total_all)) if total_all else 0
        hero = StatHero(pct="%d%%" % pct_all)
        hero.detail = (
            "%d de %d respuestas correctas" % (good_all, total_all)
            if total_all else "Responde algunos ejercicios para ver tu progreso."
        )
        box.add_widget(hero)
        for category in CATEGORIES:
            total, good = data.get(category, (0, 0))
            pct = int(round(100.0 * good / total)) if total else 0
            box.add_widget(StatRow(
                title=category,
                detail="%d/%d  •  %d%%" % (good, total, pct),
                value=pct,
                fill=list(AREA_COLORS[category]),
            ))

    def confirm_reset(self):
        if not App.get_running_app().is_admin:
            return
        confirm("Reset progress", "¿Borrar todo tu progreso?", self.do_reset)

    def do_reset(self):
        app = App.get_running_app()
        if not app.is_admin:
            return
        self.ids.stats_status.text = "Borrando el progreso sincronizado..."
        self.ids.stats_status.color = INFO_COLOR
        app.reset_progress_async(self._reset_finished)

    def _reset_finished(self, error):
        if error:
            self.ids.stats_status.text = error
            self.ids.stats_status.color = BAD_COLOR
            return
        self.ids.stats_status.text = "Progreso borrado en esta cuenta."
        self.ids.stats_status.color = OK_COLOR
        self.refresh()


class AdminScreen(Screen):
    topic_map = {}
    exercise_map = {}

    def on_pre_enter(self, *args):
        app = App.get_running_app()
        if not app.is_admin:
            self.manager.current = "home" if app.current_user else "login"
            return
        self.ids.firebase_url_input.text = (
            app.db.get_setting("firebase_db_url", "").strip() or FIREBASE_DB_URL
        )
        self.ids.firebase_storage_bucket_input.text = (
            app.db.get_setting("firebase_storage_bucket", "").strip()
            or FIREBASE_STORAGE_BUCKET
        )
        self.ids.gemini_key.text = app.db.get_setting("gemini_api_key", "")
        self.refresh_topics()

    def say(self, text, ok=True):
        color = OK_COLOR if ok else BAD_COLOR
        self.ids.status.text = text
        self.ids.status.color = color
        self.ids.status.bg = (color[0], color[1], color[2], 0.16)

    def go_back(self):
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def refresh_topics(self, *args):
        if "category" not in self.ids:
            return
        rows = App.get_running_app().db.topics(self.ids.category.text)
        self.topic_map = {row["name"]: row["id"] for row in rows}
        self.ids.topic_pick.values = list(self.topic_map)
        self.ids.topic_pick.text = next(iter(self.topic_map), "Select a topic")
        self.refresh_exercises()

    def refresh_exercises(self, selected_id=None):
        if "exercise_pick" not in self.ids:
            return
        topic_id = self.topic_map.get(self.ids.topic_pick.text)
        if topic_id is None:
            self.exercise_map = {}
        else:
            rows = App.get_running_app().db.exercises(topic_id)
            self.exercise_map = {
                "%d: %s" % (row["id"], row["prompt"][:70]): row["id"]
                for row in rows
            }
        ids = self.ids
        ids.exercise_pick.values = list(self.exercise_map)
        selected_label = next(
            (label for label, exercise_id in self.exercise_map.items()
             if exercise_id == selected_id),
            "Selecciona un ejercicio",
        )
        ids.exercise_pick.text = selected_label
        if selected_id is None:
            self.clear_exercise_fields()

    def clear_exercise_fields(self):
        for field in (self.ids.ex_prompt, self.ids.ex_passage, self.ids.ex_answer):
            field.text = ""
        self.ids.ex_mode.text = "exact"

    def save_firebase_url(self):
        if not App.get_running_app().is_admin:
            return
        url = self.ids.firebase_url_input.text.strip() or FIREBASE_DB_URL
        if not url.startswith("https://"):
            self.say("La URL de Firebase debe comenzar con https://.", False)
            return
        bucket = self.ids.firebase_storage_bucket_input.text.strip()
        if "/" in bucket or any(character.isspace() for character in bucket):
            self.say("El bucket de Storage no debe contener espacios ni barras.", False)
            return
        app = App.get_running_app()
        app.db.set_setting("firebase_db_url", url)
        app.db.set_setting("firebase_storage_bucket", bucket)
        app.firebase.database_url = url.rstrip("/")
        self.say("Configuración guardada. Publicando la biblioteca...")
        app._publish_shared_content_async(
            lambda error: self.say(
                error or "Configuración guardada y biblioteca publicada.",
                error is None,
            )
        )

    def pick_and_import_pdf(self):
        if not App.get_running_app().is_admin:
            return
        api_key = self.ids.gemini_key.text.strip()
        if not api_key:
            self.say("Pega tu API Key de Gemini antes de importar.", False)
            return
        try:
            max_pages = int(self.ids.max_pages_input.text)
        except ValueError:
            self.say("Indica un número válido de páginas.", False)
            return
        if max_pages < 1:
            self.say("El máximo de páginas debe ser al menos 1.", False)
            return

        app = App.get_running_app()
        app.db.set_setting("gemini_api_key", api_key)

        def on_error(message):
            Clock.schedule_once(lambda *_: self._import_failed(message), 0)

        def on_picked(pdf_path):
            self.ids.import_pdf_btn.disabled = True
            importer = BookImporter(app.db, app.user_images_dir)

            def on_progress(message):
                Clock.schedule_once(lambda *_: self.say(message), 0)

            def on_done(topics, exercises):
                Clock.schedule_once(
                    lambda *_: self._import_finished(topics, exercises), 0
                )

            importer.import_pdf_async(
                pdf_path, api_key, max_pages,
                on_progress=on_progress,
                on_done=on_done,
                on_error=on_error,
            )

        pick_pdf_file(app.user_data_dir, on_picked, on_error)

    def _import_finished(self, topics, exercises):
        self.ids.import_pdf_btn.disabled = False
        self.refresh_topics()
        self.say("Importación terminada. Publicando temas y ejercicios...")
        App.get_running_app()._publish_shared_content_async(
            lambda error: self.say(
                error or (
                    "Biblioteca compartida actualizada: %d temas y %d ejercicios."
                    % (topics, exercises)
                ),
                error is None,
            )
        )

    def _import_failed(self, message):
        self.ids.import_pdf_btn.disabled = False
        self.say(message, False)

    def save_topic(self):
        if not App.get_running_app().is_admin:
            return
        ids = self.ids
        name = ids.topic_name.text.strip()
        category = ids.category.text
        if not name:
            self.say("Escribe el nombre del tema primero.", False)
            return
        db = App.get_running_app().db
        if db.topic_exists(category, name):
            self.say("Ya existe un tema con ese nombre en %s." % category, False)
            return
        db.add_topic(category, name, ids.topic_description.text.strip())
        ids.topic_name.text = ""
        ids.topic_description.text = ""
        self.refresh_topics()
        ids.topic_pick.text = name
        self.say("Tema guardado. Publicando biblioteca...")
        App.get_running_app()._publish_shared_content_async(
            lambda error: self.say(
                error or "Tema publicado. Ahora puedes añadirle ejercicios.",
                error is None,
            )
        )

    def save_exercise(self):
        if not App.get_running_app().is_admin:
            return
        ids = self.ids
        topic_id = self.topic_map.get(ids.topic_pick.text)
        prompt = ids.ex_prompt.text.strip()
        answer = ids.ex_answer.text.strip()
        if topic_id is None:
            self.say("Elige un tema para el ejercicio.", False)
            return
        if not prompt or not answer:
            self.say("La pregunta y la respuesta son obligatorias.", False)
            return
        exercise_id = App.get_running_app().db.add_exercise(
            topic_id, prompt, ids.ex_passage.text.strip(), answer, "",
            ids.ex_mode.text)
        self.refresh_exercises(selected_id=exercise_id)
        self.say("Ejercicio guardado. Publicando biblioteca...")
        App.get_running_app()._publish_shared_content_async(
            lambda error: self.say(error or "Ejercicio publicado.", error is None)
        )

    def load_selected_exercise(self):
        exercise_id = self.exercise_map.get(self.ids.exercise_pick.text)
        if exercise_id is None:
            self.say("Selecciona un ejercicio primero.", False)
            return
        exercise = App.get_running_app().db.exercise(exercise_id)
        if exercise is None:
            self.refresh_exercises()
            self.say("El ejercicio ya no existe. Actualicé la lista.", False)
            return
        self.ids.ex_prompt.text = exercise["prompt"]
        self.ids.ex_passage.text = exercise["passage"] or ""
        self.ids.ex_answer.text = exercise["answer"] or ""
        self.ids.ex_mode.text = exercise["mode"] or "exact"
        self.say("Ejercicio cargado. Modifícalo y pulsa Guardar cambios.")

    def update_selected_exercise(self):
        if not App.get_running_app().is_admin:
            return
        ids = self.ids
        exercise_id = self.exercise_map.get(ids.exercise_pick.text)
        prompt = ids.ex_prompt.text.strip()
        answer = ids.ex_answer.text.strip()
        if exercise_id is None:
            self.say("Selecciona y carga un ejercicio primero.", False)
            return
        if not prompt or not answer:
            self.say("La pregunta y la respuesta son obligatorias.", False)
            return
        updated = App.get_running_app().db.update_exercise(
            exercise_id, prompt, ids.ex_passage.text.strip(), answer, ids.ex_mode.text)
        if not updated:
            self.refresh_exercises()
            self.say("El ejercicio ya no existe. Actualicé la lista.", False)
            return
        self.refresh_exercises(selected_id=exercise_id)
        self.say("Ejercicio actualizado. Publicando biblioteca...")
        App.get_running_app()._publish_shared_content_async(
            lambda error: self.say(error or "Cambios publicados.", error is None)
        )

    def confirm_delete_exercise(self):
        if not App.get_running_app().is_admin:
            return
        exercise_id = self.exercise_map.get(self.ids.exercise_pick.text)
        if exercise_id is None:
            self.say("Selecciona un ejercicio primero.", False)
            return
        exercise = App.get_running_app().db.exercise(exercise_id)
        if exercise is None:
            self.refresh_exercises()
            self.say("El ejercicio ya no existe. Actualicé la lista.", False)
            return
        confirm(
            "Eliminar ejercicio",
            "¿Eliminar este ejercicio y su progreso?\n\n%s" % exercise["prompt"],
            lambda: self.delete_exercise(exercise_id),
        )

    def delete_exercise(self, exercise_id):
        app = App.get_running_app()
        if not app.is_admin:
            return
        deleted = app.db.delete_exercise(
            exercise_id, user_id=app.current_user["uid"]
        )
        if deleted:
            app._sync_progress_async(fetch_remote=False)
            self.refresh_exercises()
            self.say("Ejercicio eliminado. Publicando biblioteca...")
            app._publish_shared_content_async(
                lambda error: self.say(
                    error or "Ejercicio eliminado de la biblioteca compartida.",
                    error is None,
                )
            )
            return
        self.refresh_exercises()
        self.say("El ejercicio ya no existe. Actualicé la lista.", False)

    def confirm_delete_topic(self):
        if not App.get_running_app().is_admin:
            return
        name = self.ids.topic_pick.text
        if name not in self.topic_map:
            self.say("Elige el tema que quieres eliminar.", False)
            return
        confirm(
            "Delete topic",
            "¿Eliminar '%s' y todos sus ejercicios?" % name,
            lambda: self.delete_topic(name),
        )

    def delete_topic(self, name):
        if not App.get_running_app().is_admin:
            return
        app = App.get_running_app()
        app.db.delete_topic(
            self.topic_map[name], user_id=app.current_user["uid"]
        )
        app._sync_progress_async(fetch_remote=False)
        self.refresh_topics()
        self.say("Tema eliminado. Publicando biblioteca...")
        app._publish_shared_content_async(
            lambda error: self.say(
                error or "Tema eliminado de la biblioteca compartida.",
                error is None,
            )
        )


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
class EnglishQuizApp(App):
    def build(self):
        self.title = "English Quiz"
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.user_images_dir = os.path.join(self.user_data_dir, "images")
        os.makedirs(self.user_images_dir, exist_ok=True)
        self.db = Database(os.path.join(self.user_data_dir, DB_NAME))
        self.speaker = Speaker()
        firebase_url = (
            self.db.get_setting("firebase_db_url", "").strip()
            or FIREBASE_DB_URL
        )
        self.firebase = FirebaseClient(FIREBASE_WEB_API_KEY, firebase_url)
        self.current_user = None
        self.id_token = ""
        self.refresh_token = ""
        self._token_expires_at = 0.0
        self._auth_lock = threading.RLock()
        self._shared_content_lock = threading.Lock()
        self.sync_status = ""
        Builder.load_string(KV)
        sm = ScreenManager(transition=SlideTransition(duration=0.2))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(PracticeHubScreen(name="practice_hub"))
        sm.add_widget(AreaScreen(name="area"))
        sm.add_widget(ExamScreen(name="exam"))
        sm.add_widget(ChatScreen(name="chat"))
        sm.add_widget(StatsScreen(name="stats"))
        sm.add_widget(AdminScreen(name="admin"))
        return sm

    @property
    def is_admin(self):
        return bool(self.current_user and self.current_user.get("role") == "admin")

    def on_start(self):
        Window.bind(on_keyboard=self.on_back)
        self._restore_session()
        Clock.schedule_interval(self._periodic_shared_content_sync, 60)

    def authenticate(self, email, password, register=False, screen_name="login"):
        def worker():
            try:
                session = (
                    self.firebase.register(email, password)
                    if register else self.firebase.sign_in(email, password)
                )
                uid = session["localId"]
                role_value = self.firebase.get_role(uid, session["idToken"])
                role = role_value or "user"
                if role not in ("user", "admin"):
                    raise FirebaseError("Firebase devolvió un rol no válido.")
                Clock.schedule_once(
                    lambda *_: self._activate_session(
                        session, role, email.strip()
                    ), 0
                )
            except (FirebaseError, KeyError, TypeError) as exc:
                error_message = str(exc)
                Clock.schedule_once(
                    lambda *_: self._show_auth_error(
                        error_message, screen_name
                    ), 0
                )

        threading.Thread(target=worker, daemon=True).start()

    def _restore_session(self):
        refresh_token = self.db.get_setting("firebase_refresh_token", "")
        saved_email = self.db.get_setting("firebase_email", "")
        if not refresh_token:
            return

        def worker():
            try:
                session = self.firebase.refresh_session(refresh_token)
                role_value = self.firebase.get_role(
                    session["localId"], session["idToken"]
                )
                role = role_value or "user"
                if role not in ("user", "admin"):
                    raise FirebaseError("Firebase devolvió un rol no válido.")
                Clock.schedule_once(
                    lambda *_: self._activate_session(
                        session, role, saved_email
                    ), 0
                )
            except (FirebaseError, KeyError, TypeError) as exc:
                error_message = str(exc)
                Clock.schedule_once(
                    lambda *_: self._show_auth_error(error_message, "login"), 0
                )

        threading.Thread(target=worker, daemon=True).start()

    def _activate_session(self, session, role, email):
        with self._auth_lock:
            self.current_user = {
                "uid": session["localId"],
                "email": email or session.get("email", ""),
                "role": role,
            }
            self.id_token = session["idToken"]
            self.refresh_token = session["refreshToken"]
            self._token_expires_at = time.time() + int(session["expiresIn"])
            self.db.set_setting("firebase_refresh_token", self.refresh_token)
            self.db.set_setting("firebase_email", self.current_user["email"])
        login = self.root.get_screen("login")
        login.ids.login_button.disabled = False
        self.root.get_screen("register").ids.register_button.disabled = False
        login.ids.password.text = ""
        self.root.transition.direction = "left"
        self.root.current = "home"
        self._set_sync_status("Sincronizando progreso...")
        self._sync_progress_async(fetch_remote=True)
        if self.is_admin:
            self._publish_shared_content_async(
                lambda error: self._set_shared_content_status(error)
                if error else None
            )
        else:
            self._sync_shared_content_async()

    def _show_auth_error(self, message, screen_name):
        screen = self.root.get_screen(screen_name)
        if screen_name == "login":
            screen.ids.login_button.disabled = False
        else:
            screen.ids.register_button.disabled = False
        screen.ids.status.text = message
        screen.ids.status.color = BAD_COLOR

    def get_id_token(self):
        with self._auth_lock:
            if self.current_user is None or not self.refresh_token:
                raise FirebaseError("Inicia sesión para conectarte a Firebase.")
            if self.id_token and self._token_expires_at > time.time() + 60:
                return self.id_token
            session = self.firebase.refresh_session(self.refresh_token)
            self.id_token = session["idToken"]
            self.refresh_token = session["refreshToken"]
            self._token_expires_at = time.time() + int(session["expiresIn"])
            self.db.set_setting("firebase_refresh_token", self.refresh_token)
            return self.id_token

    def _periodic_shared_content_sync(self, _):
        if (self.current_user is not None and not self.is_admin
                and self.root.current == "home"):
            self._sync_shared_content_async()

    @staticmethod
    def _shared_image_paths(snapshot):
        if snapshot is None:
            return set()
        if not isinstance(snapshot, dict) or snapshot.get("version") != 1:
            raise FirebaseError("Firebase devolvió una biblioteca compartida no válida.")
        topics = snapshot.get("topics", [])
        if topics is None:
            return set()
        if not isinstance(topics, list):
            raise FirebaseError("Firebase devolvió una biblioteca compartida no válida.")
        paths = set()
        for topic in topics:
            if not isinstance(topic, dict) or not isinstance(topic.get("exercises"), list):
                raise FirebaseError("Firebase devolvió un tema compartido no válido.")
            for exercise in topic["exercises"]:
                if not isinstance(exercise, dict):
                    raise FirebaseError("Firebase devolvió un ejercicio compartido no válido.")
                image_path = exercise.get("image_file", "")
                if not isinstance(image_path, str):
                    raise FirebaseError("Firebase devolvió una imagen no válida.")
                if image_path:
                    parts = image_path.split("/")
                    filename = parts[-1] if parts else ""
                    if (len(parts) != 3 or parts[0] != "shared-content"
                            or len(parts[1]) == 0 or len(filename) != 68
                            or not filename.endswith(".jpg")
                            or any(char not in "0123456789abcdef"
                                   for char in filename[:-4])):
                        raise FirebaseError(
                            "Firebase devolvió una ruta de imagen compartida no válida."
                        )
                    paths.add(image_path)
        return paths

    def _sync_shared_content_async(self):
        if self.current_user is None or self.is_admin:
            return
        if not self._shared_content_lock.acquire(False):
            return

        def worker():
            try:
                token = self.get_id_token()
                remote_snapshot = self.firebase.get_shared_content(token)
                self._shared_image_paths(remote_snapshot)
                snapshot = remote_snapshot or {"version": 1, "topics": []}
                remote_topics = snapshot.get("topics")
                if remote_topics is None:
                    remote_topics = []
                if not isinstance(remote_topics, list):
                    raise FirebaseError(
                        "Firebase devolvió una biblioteca compartida no válida."
                    )
                fingerprint = hashlib.sha256(
                    json.dumps(
                        snapshot, sort_keys=True, separators=(",", ":")
                    ).encode("utf-8")
                ).hexdigest()
                if self.db.get_setting("shared_content_fingerprint", "") == fingerprint:
                    message = "Contenido compartido actualizado."
                    Clock.schedule_once(
                        lambda *_: self._set_shared_content_status(message), 0
                    )
                    return

                local_topics = []
                bucket = (
                    self.db.get_setting("firebase_storage_bucket", "").strip()
                    or FIREBASE_STORAGE_BUCKET
                )
                for topic in remote_topics:
                    if not isinstance(topic, dict) or not isinstance(
                            topic.get("exercises"), list):
                        raise FirebaseError(
                            "Firebase devolvió un tema compartido no válido."
                        )
                    local_topic = dict(topic)
                    local_topic["exercises"] = []
                    for exercise in topic["exercises"]:
                        if not isinstance(exercise, dict):
                            raise FirebaseError(
                                "Firebase devolvió un ejercicio compartido no válido."
                            )
                        local_exercise = dict(exercise)
                        image_path = local_exercise.get("image_file", "")
                        if image_path:
                            self._shared_image_paths({
                                "version": 1,
                                "topics": [{
                                    "exercises": [{"image_file": image_path}]
                                }],
                            })
                            filename = image_path.rsplit("/", 1)[-1]
                            image_digest = filename[:-4]
                            local_filename = "shared_%s.jpg" % image_digest
                            image_path_on_device = os.path.join(
                                self.user_images_dir, local_filename
                            )
                            valid_cached_file = False
                            if os.path.isfile(image_path_on_device):
                                with open(image_path_on_device, "rb") as image_file:
                                    valid_cached_file = (
                                        hashlib.sha256(image_file.read()).hexdigest()
                                        == image_digest
                                    )
                            if not valid_cached_file:
                                image_bytes = self.firebase.download_shared_image(
                                    bucket, image_path, token
                                )
                                if hashlib.sha256(image_bytes).hexdigest() != image_digest:
                                    raise FirebaseError(
                                        "La imagen compartida no coincide con su identificador."
                                    )
                                temporary_path = image_path_on_device + ".tmp"
                                with open(temporary_path, "wb") as image_file:
                                    image_file.write(image_bytes)
                                os.replace(temporary_path, image_path_on_device)
                            local_exercise["image_file"] = local_filename
                        local_topic["exercises"].append(local_exercise)
                    local_topics.append(local_topic)

                self.db.replace_shared_content(local_topics)
                self.db.set_setting("shared_content_fingerprint", fingerprint)
                message = "Contenido compartido actualizado."
            except (FirebaseError, ValueError, OSError, sqlite3.Error) as exc:
                message = "Contenido compartido pendiente: %s" % exc
            finally:
                self._shared_content_lock.release()
            Clock.schedule_once(
                lambda *_: self._set_shared_content_status(message), 0
            )

        threading.Thread(target=worker, daemon=True).start()

    def _publish_shared_content_async(self, callback=None):
        if self.current_user is None or not self.is_admin:
            if callback:
                callback("Solo el administrador puede publicar contenido.")
            return

        user_id = self.current_user["uid"]

        def worker():
            message = None
            try:
                with self._shared_content_lock:
                    token = self.get_id_token()
                    previous = self.firebase.get_shared_content(token)
                    previous_paths = self._shared_image_paths(previous)
                    snapshot = self.db.shared_content_snapshot()
                    snapshot["revision"] = uuid.uuid4().hex
                    bucket = (
                        self.db.get_setting("firebase_storage_bucket", "").strip()
                        or FIREBASE_STORAGE_BUCKET
                    )
                    new_paths = set()
                    for topic in snapshot["topics"]:
                        for exercise in topic["exercises"]:
                            image_name = exercise["image_file"]
                            if not image_name:
                                continue
                            if os.path.basename(image_name) != image_name:
                                raise ValueError(
                                    "La biblioteca contiene un nombre de imagen no válido."
                                )
                            image_path = os.path.join(
                                self.user_images_dir, image_name
                            )
                            if not os.path.isfile(image_path):
                                image_path = os.path.join(BUNDLED_IMAGE_DIR, image_name)
                            if not os.path.isfile(image_path):
                                raise ValueError(
                                    "No se encuentra la imagen del ejercicio: %s"
                                    % image_name
                                )
                            with open(image_path, "rb") as image_file:
                                image_bytes = image_file.read()
                            if len(image_bytes) >= 10 * 1024 * 1024:
                                raise ValueError(
                                    "La imagen supera el límite de 10 MB de Firebase Storage."
                                )
                            digest = hashlib.sha256(image_bytes).hexdigest()
                            object_name = "shared-content/%s/%s.jpg" % (
                                user_id, digest
                            )
                            self.firebase.upload_shared_image(
                                bucket, object_name, image_bytes, token
                            )
                            exercise["image_file"] = object_name
                            new_paths.add(object_name)
                    self.firebase.put_shared_content(snapshot, token)
                    stale_paths = previous_paths - new_paths
                    cleanup_errors = []
                    for object_name in stale_paths:
                        if object_name.split("/")[1] != user_id:
                            continue
                        try:
                            self.firebase.delete_shared_image(
                                bucket, object_name, token
                            )
                        except FirebaseError as exc:
                            cleanup_errors.append(str(exc))
                message = (
                    "Biblioteca publicada, pero no se pudieron limpiar algunas "
                    "imágenes antiguas: %s" % "; ".join(cleanup_errors)
                    if cleanup_errors else None
                )
            except (FirebaseError, ValueError, OSError, sqlite3.Error) as exc:
                message = "No se pudo publicar el contenido: %s" % exc
            if callback:
                Clock.schedule_once(lambda *_: callback(message), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _set_shared_content_status(self, message):
        self.sync_status = message
        if self.root.current == "home":
            self.root.get_screen("home").ids.home_sync_status.text = message

    def record_attempt(self, exercise_id, correct):
        if self.current_user is None:
            raise FirebaseError("Inicia sesión para guardar tu progreso.")
        self.db.record_attempt(
            exercise_id, correct, user_id=self.current_user["uid"]
        )
        self._sync_progress_async(fetch_remote=False)

    def _sync_progress_async(self, fetch_remote=False):
        if self.current_user is None:
            return
        user_id = self.current_user["uid"]

        def worker():
            errors = []
            try:
                deletion_cutoffs = self.db.pending_progress_deletions(user_id)
                if deletion_cutoffs:
                    self.firebase.delete_progress_for_exercises(
                        user_id, deletion_cutoffs, self.get_id_token()
                    )
                    self.db.mark_progress_deletions_synced(
                        user_id, deletion_cutoffs
                    )
                if fetch_remote:
                    token = self.get_id_token()
                    remote = self.firebase.get_progress(user_id, token)
                    self.db.merge_remote_progress(user_id, remote)
                for event_id, event in self.db.pending_progress(user_id):
                    token = self.get_id_token()
                    try:
                        self.firebase.put_progress_event(
                            user_id, event_id, event, token
                        )
                        self.db.mark_progress_synced(user_id, event_id)
                    except FirebaseError as exc:
                        errors.append(str(exc))
                message = (
                    "Progreso sincronizado." if not errors
                    else "Sincronización pendiente: %s" % "; ".join(errors)
                )
            except (FirebaseError, ValueError, sqlite3.Error) as exc:
                message = "Sincronización pendiente: %s" % exc
            Clock.schedule_once(
                lambda *_: self._set_sync_status(message), 0
            )

        threading.Thread(target=worker, daemon=True).start()

    def _set_sync_status(self, message):
        self.sync_status = message
        if self.root.current == "home":
            home = self.root.get_screen("home")
            home.ids.home_sync_status.text = message
            home.on_pre_enter()

    def reset_progress_async(self, callback):
        if self.current_user is None:
            callback("Inicia sesión para borrar el progreso.")
            return
        user_id = self.current_user["uid"]

        def worker():
            try:
                self.firebase.delete_progress(user_id, self.get_id_token())
                self.db.reset_progress(user_id)
                error = None
            except (FirebaseError, sqlite3.Error) as exc:
                error = "No se pudo borrar el progreso sincronizado: %s" % exc
            Clock.schedule_once(lambda *_: callback(error), 0)

        threading.Thread(target=worker, daemon=True).start()

    def logout(self):
        chat = self.root.get_screen("chat")
        if chat.chat_client is not None:
            chat.chat_client.leave_room()
        with self._auth_lock:
            self.current_user = None
            self.id_token = ""
            self.refresh_token = ""
            self._token_expires_at = 0.0
        self.db.set_setting("firebase_refresh_token", "")
        self.db.set_setting("firebase_email", "")
        login = self.root.get_screen("login")
        login.ids.password.text = ""
        login.ids.status.text = ""
        self.root.transition.direction = "right"
        self.root.current = "login"

    def on_back(self, window, key, *args):
        if key == 27 and self.root.current == "register":
            self.root.transition.direction = "right"
            self.root.current = "login"
            return True
        if key == 27 and self.root.current not in ("home", "login"):
            self.root.transition.direction = "right"
            self.root.current = "home"
            return True
        return False

    def on_stop(self):
        self.speaker.shutdown()
        self.db.conn.close()


if __name__ == "__main__":
    EnglishQuizApp().run()