"""English Quiz - app de práctica de inglés (nivel A1) hecha con Kivy.

Áreas: Reading, Listening, Speaking, Writing, Conversations.
Incluye: base de datos SQLite, progreso/estadísticas, administración de
temas y ejercicios, validación de respuestas mejorada y audio/TTS opcional.

Dependencias: kivy. La voz (Listening/Speaking) usa el texto a voz del propio
dispositivo, así que no hace falta subir audios.
"""
import os
import re
import sqlite3
import unicodedata

from kivy.app import App
from kivy.lang import Builder
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
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
    # Que el teclado del celular no tape el cuadro de respuesta
    Window.softinput_mode = "below_target"

DB_NAME = "english_quiz.db"
SEED_VERSION = 5  # 1 = original, 2 = + Units 3 & 4, 3 = modelo de voz, 4 = Listening sin pistas, 5 = 25 por apartado
# Textos antiguos que se reemplazan en bases de datos ya creadas
PROMPT_FIXES = [
    ("Listen and write the place that is next to the school.",
     "Listen and write the place they are asking about."),
]
PASSAGE_FIXES = [
    ("My name is... I am ... years old. I am from...",
     "Modelo: My name is Daniel. I am 25 years old. I am from Colombia."),
]
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio")
CATEGORIES = ["Reading", "Listening", "Speaking", "Writing", "Conversations"]

DESCRIPTIONS = {
    "Reading": "Lee el texto y responde la pregunta.",
    "Listening": "Toca Play audio, escucha con atención y escribe lo que se pide. Puedes repetirlo o ponerlo más lento.",
    "Speaking": "Escucha el modelo, dilo en voz alta y escribe lo que dijiste.",
    "Writing": "Completa palabras y frases escribiendo la respuesta.",
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

# Color de cada área (el mismo que usan las tarjetas del inicio)
AREA_COLORS = {
    "Reading": (0.20, 0.47, 0.93, 1),
    "Listening": (0.55, 0.36, 0.96, 1),
    "Speaking": (0.13, 0.67, 0.50, 1),
    "Writing": (0.95, 0.55, 0.20, 1),
    "Conversations": (0.08, 0.64, 0.74, 1),
}

Window.clearcolor = BG


# --------------------------------------------------------------------------
# Componentes visuales (su apariencia está definida en el KV)
# --------------------------------------------------------------------------
class RBtn(Button):
    """Botón con esquinas redondeadas; el color se cambia con 'bg'."""
    bg = ListProperty([0.20, 0.47, 0.93, 1])


class Tile(Button):
    """Tarjeta grande de color del inicio."""
    bg = ListProperty([0.20, 0.47, 0.93, 1])


class Card(BoxLayout):
    bg = ListProperty([0.090, 0.118, 0.196, 1])


class Banner(Label):
    """Mensaje con fondo suave del mismo color que el texto."""
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

# --------------------------------------------------------------------------
# Datos iniciales: categoría -> [(tema, descripción, [(prompt, passage,
#                                respuesta, audio, modo), ...]), ...]
# En 'respuesta' se pueden poner alternativas separadas por "|".
# modo: 'exact' (igual) o 'contains' (la respuesta contiene la frase clave).
# --------------------------------------------------------------------------
SEED = {
    "Reading": [
        ("Personal information", "Lee perfiles personales cortos.", [
            ("What is the person's name?",
             "Hello! My name is Daniel. I am 25 years old. I am from Colombia.",
             "Daniel", "", "exact"),
            ("How old is Anna?",
             "Hi! I'm Anna. I'm 19 years old. I live in Madrid with my family.",
             "19|nineteen|19 years old|she is 19|she's 19", "", "exact"),
            ("Where is Tom from?",
             "This is Tom. He is from Canada. He is a teacher.",
             "Canada|he is from canada|he's from canada", "", "exact"),
        ]),
        ("Daily routine", "Textos sobre la rutina diaria.", [
            ("What time does Laura get up?",
             "Laura gets up at 6:30. She eats breakfast at 7:00 and goes to work at 8:00.",
             "6:30|6.30|half past six|at 6:30", "", "exact"),
            ("What does Laura do at 7:00?",
             "Laura gets up at 6:30. She eats breakfast at 7:00 and goes to work at 8:00.",
             "eats breakfast|she eats breakfast|breakfast|has breakfast", "", "exact"),
        ]),
    ],
    "Listening": [
        ("At the bank", "Escucha una conversación corta.", [
            ("Listen and write the place.",
             "A: Excuse me. Where's the bank? B: It's around the corner.",
             "bank|the bank", "bank.mp3", "exact"),
        ]),
        ("Numbers", "Escucha y escribe los números.", [
            ("Listen and write the number (in digits).",
             "My phone number is five, five, five, one, two, three.",
             "555123|555 123|5 5 5 1 2 3|five five five one two three", "", "exact"),
            ("Listen and write the age (in digits).",
             "I am thirty years old.",
             "30|thirty", "", "exact"),
        ]),
    ],
    "Speaking": [
        ("Introduce yourself", "Preséntate en inglés.", [
            ("Say your name, age and city in English. Then type what you said.",
             "Modelo: My name is Daniel. I am 25 years old. I am from Colombia.",
             "my name is", "", "contains"),
        ]),
        ("Greetings", "Saludos y despedidas básicas.", [
            ("Greet someone in the morning. Type what you said.",
             "Good morning! How are you?",
             "good morning|hello|hi", "", "contains"),
            ("Say goodbye to a friend. Type what you said.",
             "Goodbye! See you tomorrow.",
             "goodbye|bye|see you", "", "contains"),
        ]),
    ],
    "Writing": [
        ("Verb to be", "Afirmativo y negativo.", [
            ("Complete: She ____ a student.",
             "Pista: usa la forma correcta del verbo to be.", "is", "", "exact"),
            ("Complete: I ____ from Colombia.",
             "Pista: usa la forma correcta del verbo to be.", "am", "", "exact"),
            ("Complete: They ____ not at home.",
             "Pista: usa la forma correcta del verbo to be.", "are", "", "exact"),
        ]),
        ("Plurals", "Plurales regulares e irregulares.", [
            ("Write the plural of 'book'.", "Pista: agrega -s.", "books", "", "exact"),
            ("Write the plural of 'child'.", "Pista: es irregular.", "children", "", "exact"),
        ]),
    ],
    "Conversations": [
        ("Asking for directions", "Practica un diálogo con un compañero.", [
            ("Complete: It's ____ the supermarket.",
             "Expresiones útiles: next to, behind, in front of, near.",
             "next to|behind|in front of|near", "", "exact"),
            ("Complete: Excuse me, where ____ the station?",
             "Expresiones útiles: is / are.", "is", "", "exact"),
        ]),
        ("At the restaurant", "Pedir comida y bebida.", [
            ("Complete: I ____ like a coffee, please.",
             "Expresión cortés para pedir algo.", "would|'d", "", "exact"),
            ("Complete: Can I have the ____, please? (to pay)",
             "Al final de la comida.", "bill|check", "", "exact"),
        ]),
    ],
}

# --------------------------------------------------------------------------
# Review - Units 3 & 4: Places, Directions, Transportation and Family
# (mismo formato que SEED; se fusiona con él justo debajo)
# --------------------------------------------------------------------------
UNITS_3_4 = {
    "Reading": [
        ("Unit 3 - Places in the city", "Lugares de la ciudad.", [
            ("Where do you buy medicine?",
             "A pharmacy is where you buy medicine. A newsstand is where you buy "
             "newspapers and magazines.",
             "pharmacy|a pharmacy|the pharmacy|at the pharmacy", "", "exact"),
            ("Where do you keep your money?",
             "A bank is where you keep your money. A school is where you study and learn.",
             "bank|a bank|the bank|at the bank", "", "exact"),
            ("Where do you buy books?",
             "A bookstore is where you buy books. A restaurant is where you eat food.",
             "bookstore|a bookstore|the bookstore|at the bookstore", "", "exact"),
            ("Where is the pharmacy?",
             "A: Where's the pharmacy?\nB: It's across the street.",
             "across the street|it's across the street|it is across the street",
             "", "exact"),
        ]),
        ("Unit 3 - Transportation", "Medios de transporte con BY.", [
            ("How does the speaker go to school?",
             "I go to school by bus. My brother goes to work by train. "
             "We say 'on foot', not 'by foot'.",
             "by bus|bus|on the bus|i go by bus", "", "exact"),
            ("How does the speaker's brother go to work?",
             "I go to school by bus. My brother goes to work by train. "
             "We say 'on foot', not 'by foot'.",
             "by train|train|on the train|he goes by train", "", "exact"),
            ("Which is correct: 'by foot' or 'on foot'?",
             "We use BY with vehicles: by taxi, by bus, by car. The exception is 'on foot'.",
             "on foot", "", "exact"),
        ]),
        ("Unit 4 - Family", "Lee sobre una familia.", [
            ("Who is Louise?",
             "This is my family. My dad is Carlos. He's 45 years old. My mom is Louise. "
             "She's 42. I have one sister. She's 18 and very pretty.",
             "mom|my mom|the mom|mother|my mother|she's my mom|she is my mom", "", "exact"),
            ("How old is the mom?",
             "This is my family. My dad is Carlos. He's 45 years old. My mom is Louise. "
             "She's 42. I have one sister. She's 18 and very pretty.",
             "42|forty-two|forty two|42 years old|she's 42|she is 42", "", "exact"),
            ("How many sisters does the speaker have?",
             "This is my family. My dad is Carlos. He's 45 years old. My mom is Louise. "
             "She's 42. I have one sister. She's 18 and very pretty.",
             "one|1|one sister|1 sister|she has one|i have one sister", "", "exact"),
            ("How old is the sister?",
             "This is my family. My dad is Carlos. He's 45 years old. My mom is Louise. "
             "She's 42. I have one sister. She's 18 and very pretty.",
             "18|eighteen|18 years old|she's 18|she is 18", "", "exact"),
        ]),
    ],
    "Listening": [
        ("Unit 3 - Directions", "Escucha dónde están los lugares.", [
            ("Listen and write the place they are asking about.",
             "A: Where's the bookstore? B: It's next to the school.",
             "bookstore|the bookstore|a bookstore", "", "exact"),
            ("Listen and write where the restaurant is.",
             "A: Where's the restaurant? B: It's around the corner.",
             "around the corner|it's around the corner|it is around the corner",
             "", "exact"),
            ("Listen and write where the pharmacy is.",
             "A: Where's the pharmacy? B: It's across the street.",
             "across the street|it's across the street|it is across the street",
             "", "exact"),
        ]),
        ("Unit 3 - Transportation", "Escucha cómo viaja cada persona.", [
            ("Listen and write how the person goes to work.",
             "I go to work by train.",
             "by train|train|on the train", "", "exact"),
            ("Listen. How does she go to school?",
             "She goes to school on foot.",
             "on foot|she goes on foot|walking|she walks|walks", "", "exact"),
            ("Listen and write the transportation.",
             "My brother goes to the park by bicycle.",
             "by bicycle|bicycle|bike|by bike|on a bicycle", "", "exact"),
        ]),
        ("Unit 4 - Family and ages", "Escucha edades y parentescos.", [
            ("Listen and write the age (in digits).",
             "A: How old is your sister? B: She's eighteen.",
             "18|eighteen|she's 18|she's eighteen|she is 18", "", "exact"),
            ("Listen and write the number (in digits).",
             "A: How old are they? B: They're fifty.",
             "50|fifty|they're 50|they're fifty|they are 50", "", "exact"),
            ("Listen and write who he is.",
             "A: Who is he? B: He's my dad.",
             "dad|my dad|father|my father|he's my dad|he is my dad", "", "exact"),
        ]),
    ],
    "Speaking": [
        ("Unit 3 - Places and directions", "Di dónde queda cada lugar.", [
            ("Where's the pharmacy? Answer with a direction expression. "
             "Then type what you said.",
             "Modelo: It's across the street.",
             "across the street|next to|around the corner|down the street|"
             "on the left|on the right|between", "", "contains"),
            ("Say where the bookstore is, using 'next to'. Then type what you said.",
             "Modelo: The bookstore is next to the school.",
             "next to", "", "contains"),
            ("Ask a partner where the bank is. Then type what you said.",
             "Modelo: Where's the bank?",
             "where's the bank|where is the bank", "", "contains"),
        ]),
        ("Unit 3 - How do you go?", "Habla de tu transporte.", [
            ("Say how you go to school or work. Use 'by'. Then type what you said.",
             "Modelo: I go to work by bus.",
             "by|on foot", "", "contains"),
            ("Say how you go to a place near your house. Then type what you said.",
             "Modelo: I go to the pharmacy on foot.",
             "by|on foot", "", "contains"),
        ]),
        ("Unit 4 - My family", "Habla de tu familia.", [
            ("Say who is in your family. Then type what you said.",
             "Modelo: I have one brother and one sister. My mom is Louise.",
             "i have|my", "", "contains"),
            ("Say how old a family member is. Then type what you said.",
             "Modelo: He's twenty years old.",
             "she's|he's|they're|years old|old", "", "contains"),
            ("Ask your partner who is in their family. Then type what you said.",
             "Modelo: Who is in your family?",
             "who is|who's|who are", "", "contains"),
        ]),
    ],
    "Writing": [
        ("Unit 3 - Where questions", "Preguntas con Where y direcciones.", [
            ("Complete: ____ the bank? (short form of Where is)",
             "Pista: Where's + the place.", "where's|where is", "", "exact"),
            ("Complete: It's ____ the street. (on the other side of the road)",
             "Pista: across the street.", "across", "", "exact"),
            ("Complete: It's ____ the corner. (you need to turn to find it)",
             "Pista: around the corner.", "around", "", "exact"),
            ("Complete: The restaurant is ____ the bank and the school. "
             "(in the middle of two places)",
             "Pista: la palabra significa 'entre'.", "between", "", "exact"),
        ]),
        ("Unit 3 - Imperatives", "Imperativos para dar direcciones.", [
            ("Complete: ____ to the bank. (go on foot)",
             "Pista: usa el verbo base, sin sujeto.", "walk", "", "exact"),
            ("Complete: ____ the bus to the school.",
             "Pista: Take + transporte.", "take", "", "exact"),
            ("Make it negative: ____ drive.",
             "Pista: forma negativa del imperativo.", "don't|do not", "", "exact"),
        ]),
        ("Unit 3 - BY + transportation", "Usa BY o 'on foot'.", [
            ("Complete: I go to school ____ bus.",
             "Pista: no se usa 'a' ni 'the' después.", "by", "", "exact"),
            ("Complete: She goes to work ____ foot.",
             "Pista: es la excepción: no se dice 'by foot'.", "on", "", "exact"),
            ("Complete: He goes to the park ____ car.",
             "Pista: BY + vehículo.", "by", "", "exact"),
        ]),
        ("Unit 4 - Who questions", "Preguntas con Who.", [
            ("Complete: ____ is he? He's my dad.",
             "Pista: pregunta por personas.", "who", "", "exact"),
            ("Complete: ____ Louise? She's my mom. (short form of Who is)",
             "Pista: forma corta de Who is.", "who's", "", "exact"),
            ("Complete: Who ____ they? They're my sisters.",
             "Pista: dos o más personas.", "are", "", "exact"),
        ]),
        ("Unit 4 - Have / has", "Have para I/you/we/they, has para he/she/it.", [
            ("Complete: I ____ a brother.", "Pista: have o has.", "have", "", "exact"),
            ("Complete: She ____ one brother.", "Pista: he, she, it usan has.",
             "has", "", "exact"),
            ("Complete: My mom ____ three siblings.", "Pista: my mom = she.",
             "has", "", "exact"),
            ("Complete: We ____ cousins.", "Pista: we usa have.", "have", "", "exact"),
        ]),
        ("Unit 4 - Describing people and ages", "Adjetivos y edades.", [
            ("Write the opposite of 'short'.", "Pista: describe la altura.",
             "tall", "", "exact"),
            ("Write the opposite of 'old'.", "Pista: describe la edad.",
             "young", "", "exact"),
            ("Complete: How ____ is your sister?", "Pista: pregunta por la edad.",
             "old", "", "exact"),
            ("Complete: How old ____ they?", "Pista: dos o más personas.",
             "are", "", "exact"),
            ("Write 33 in words.", "Pista: thirty-...",
             "thirty-three|thirty three", "", "exact"),
        ]),
    ],
    "Conversations": [
        ("Unit 3 - Where's the...?", "Preguntar y dar la ubicación de un lugar.", [
            ("A: Where's the pharmacy?  B: It's ____ the street.",
             "Significa: al otro lado de la calle.", "across", "", "exact"),
            ("A: Where's the bookstore?  B: It's ____ the school.",
             "Expresiones útiles: next to, between, across the street.",
             "next to", "", "exact"),
            ("A: Where's the restaurant?  B: It's ____ the street.",
             "Significa: más adelante por la misma calle.", "down", "", "exact"),
            ("A: How do I get to the bank?  B: ____ across the street.",
             "Imperativo: ir a pie.", "walk", "", "exact"),
        ]),
        ("Unit 3 - Getting around", "Hablar del transporte.", [
            ("A: How do you go to work?  B: I go ____ bus.",
             "BY + transporte.", "by", "", "exact"),
            ("A: How ____ I get to the school?  B: Take the bus.",
             "Pregunta para pedir direcciones.", "do", "", "exact"),
            ("A: Do you drive?  B: No. I ____ the subway.",
             "Verbo para subirse a un transporte público.", "take", "", "exact"),
        ]),
        ("Unit 4 - Talking about family", "Conversar sobre la familia.", [
            ("A: Who is he?  B: ____ my dad.",
             "Forma corta de He is.", "he's|he is", "", "exact"),
            ("A: How old is your sister?  B: ____ 18.",
             "Forma corta de She is.", "she's|she is", "", "exact"),
            ("A: Who are they?  B: ____ my sisters.",
             "Forma corta de They are.", "they're|they are", "", "exact"),
            ("A: Does she have a brother?  B: Yes, she ____ one brother.",
             "she usa has.", "has", "", "exact"),
        ]),
    ],
}

for _category, _topics in UNITS_3_4.items():
    SEED[_category].extend(_topics)

# 25 ejercicios por apartado en cada unidad (están en units_data.py)
from units_data import EXTRA_UNITS_3_4  # noqa: E402

for _category, _topics in EXTRA_UNITS_3_4.items():
    SEED[_category].extend(_topics)


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def normalize(text):
    """Minúsculas, sin acentos ni puntuación, espacios colapsados."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"[^\w\s':]", " ", text.replace("’", "'"))
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

# ---------------------------------------------------------------- base
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
    height: dp(28)
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
        # IMPORTANTE: TextInput pinta su texto con el último Color de canvas.before.
        # Hay que devolverle su color después de dibujar el fondo; si no, el texto
        # sale del mismo color que el fondo y no se ve.
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text and not self.focus else self.foreground_color)
    canvas.after:
        Color:
            rgba: C_PRIMARY if self.focus else C_LINE
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(12))
            width: 1.1
        # El cursor propio original queda tapado por el fondo, así que se dibuja aquí.
        Color:
            rgba: C_PRIMARY if self.focus else (0, 0, 0, 0)
        Rectangle:
            pos: self.cursor_pos
            size: self.cursor_width, self.line_height + self.line_spacing

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

# ---------------------------------------------------------------- inicio
<MainScreen>:
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
                    height: dp(78)
                    Label:
                        text: 'English Quiz'
                        bold: True
                        font_size: '30sp'
                        color: C_TEXT
                        text_size: self.size
                        halign: 'left'
                        valign: 'bottom'
                    Label:
                        text: 'Nivel A1  •  Learn, practice, improve'
                        font_size: '14sp'
                        color: C_MUTED
                        text_size: self.size
                        halign: 'left'
                        valign: 'top'
                Card:
                    BoxLayout:
                        size_hint_y: None
                        height: dp(66)
                        spacing: dp(10)
                        BoxLayout:
                            orientation: 'vertical'
                            Label:
                                text: 'TU PROGRESO'
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
                                font_size: '34sp'
                                color: C_TEXT
                                text_size: self.size
                                halign: 'left'
                                valign: 'middle'
                        RBtn:
                            text: 'Detalles'
                            size_hint_x: None
                            width: dp(96)
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
                Section:
                    text: 'ELIGE UN ÁREA'
                GridLayout:
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
                        text: '[b][size=19sp]Manage[/size][/b]\n[size=12sp][color=dfe9f7]Temas y ejercicios[/color][/size]'
                        bg: 0.30, 0.35, 0.46, 1
                        on_release: root.go('admin')

# ---------------------------------------------------------------- práctica
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
                on_release: root.go_home()
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
                    spacing: dp(8)
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
                    height: dp(100)
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
                Banner:
                    id: feedback
                    text: ''

# ---------------------------------------------------------------- progreso
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
                on_release: root.manager.current = 'home'
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
        RBtn:
            text: 'Reset progress'
            bg: 0.62, 0.20, 0.22, 1
            on_release: root.confirm_reset()

# ---------------------------------------------------------------- administración
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
                on_release: root.manager.current = 'home'
            Label:
                text: 'Manage topics'
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
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(12)
                padding: [0, dp(4), 0, dp(24)]
                Card:
                    Section:
                        text: 'ÁREA DE APRENDIZAJE'
                    RSpinner:
                        id: category
                        text: 'Reading'
                        values: ['Reading', 'Listening', 'Speaking', 'Writing', 'Conversations']
                        on_text: root.refresh_topics()
                Card:
                    Section:
                        text: 'NUEVO TEMA'
                    Field:
                        id: topic_name
                        hint_text: 'Nombre del tema (ej. Family)'
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
                        text: 'NUEVO EJERCICIO'
                    RSpinner:
                        id: topic_pick
                        text: 'Select a topic'
                        values: []
                    Field:
                        id: ex_prompt
                        hint_text: 'Pregunta / instrucción'
                        multiline: True
                        height: dp(76)
                    Field:
                        id: ex_passage
                        hint_text: 'Texto o transcripción (en Listening se lee en voz alta)'
                        multiline: True
                        height: dp(76)
                    Field:
                        id: ex_answer
                        hint_text: 'Respuesta (alternativas con |  ej: is|it is)'
                    RSpinner:
                        id: ex_mode
                        text: 'exact'
                        values: ['exact', 'contains']
                    RBtn:
                        text: 'Save exercise'
                        bg: C_PRIMARY
                        on_release: root.save_exercise()
                RBtn:
                    text: 'Delete selected topic'
                    bg: 0.62, 0.20, 0.22, 1
                    on_release: root.confirm_delete_topic()
                Banner:
                    id: status
                    text: 'Los datos se guardan en este dispositivo.'
                    color: C_MUTED
"""


# --------------------------------------------------------------------------
# Base de datos
# --------------------------------------------------------------------------
class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()
        self.seed()

    def create_tables(self):
        c = self.conn
        c.execute("""CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            UNIQUE(category, name))""")
        c.execute("""CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            passage TEXT DEFAULT '',
            answer TEXT NOT NULL,
            audio_file TEXT DEFAULT '',
            mode TEXT DEFAULT 'exact',
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE)""")
        c.execute("""CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise_id INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE CASCADE)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_topics_cat ON topics(category)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ex_topic ON exercises(topic_id)")
        c.commit()

    def seed(self):
        """Carga los temas incluidos. Solo agrega los que faltan, así una
        actualización de la app suma unidades nuevas sin duplicar nada ni
        tocar el progreso. Cada vez que se agregue contenido, sube SEED_VERSION."""
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        if version >= SEED_VERSION:
            return
        for category, topics in SEED.items():
            for name, desc, exercises in topics:
                if self.topic_exists(category, name):
                    continue
                tid = self.add_topic(category, name, desc)
                for prompt, passage, answer, audio, mode in exercises:
                    self.add_exercise(tid, prompt, passage, answer, audio, mode)
        for old, new in PASSAGE_FIXES:
            self.conn.execute("UPDATE exercises SET passage=? WHERE passage=?", (new, old))
        for old, new in PROMPT_FIXES:
            self.conn.execute("UPDATE exercises SET prompt=? WHERE prompt=?", (new, old))
        self.conn.execute("PRAGMA user_version = %d" % SEED_VERSION)
        self.conn.commit()

    # --- temas / ejercicios
    def topics(self, category):
        return self.conn.execute(
            "SELECT * FROM topics WHERE category=? ORDER BY name", (category,)).fetchall()

    def exercises(self, topic_id):
        return self.conn.execute(
            "SELECT * FROM exercises WHERE topic_id=? ORDER BY id", (topic_id,)).fetchall()

    def add_topic(self, category, name, description=""):
        cur = self.conn.execute(
            "INSERT INTO topics(category,name,description) VALUES(?,?,?)",
            (category, name, description))
        self.conn.commit()
        return cur.lastrowid

    def topic_exists(self, category, name):
        return self.conn.execute(
            "SELECT 1 FROM topics WHERE category=? AND lower(name)=lower(?)",
            (category, name)).fetchone() is not None

    def add_exercise(self, topic_id, prompt, passage, answer, audio="", mode="exact"):
        self.conn.execute(
            "INSERT INTO exercises(topic_id,prompt,passage,answer,audio_file,mode) "
            "VALUES(?,?,?,?,?,?)", (topic_id, prompt, passage, answer, audio, mode))
        self.conn.commit()

    def delete_topic(self, topic_id):
        self.conn.execute("DELETE FROM topics WHERE id=?", (topic_id,))
        self.conn.commit()

    # --- progreso
    def record_attempt(self, exercise_id, correct):
        self.conn.execute("INSERT INTO attempts(exercise_id,correct) VALUES(?,?)",
                          (exercise_id, 1 if correct else 0))
        self.conn.commit()

    def stats(self):
        rows = self.conn.execute("""
            SELECT t.category AS category, COUNT(a.id) AS total,
                   COALESCE(SUM(a.correct), 0) AS good
            FROM attempts a
            JOIN exercises e ON e.id = a.exercise_id
            JOIN topics t ON t.id = e.topic_id
            GROUP BY t.category""").fetchall()
        return {r["category"]: (r["total"], r["good"]) for r in rows}

    def reset_progress(self):
        self.conn.execute("DELETE FROM attempts")
        self.conn.commit()


# --------------------------------------------------------------------------
# Utilidad de confirmación
# --------------------------------------------------------------------------
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
# Pantallas
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# Voz: lee los textos en voz alta con la voz del propio dispositivo
# --------------------------------------------------------------------------
MSG_NO_ENGINE = ("No se pudo iniciar la voz del teléfono. Revisa en Ajustes > Idioma > "
                 "Texto a voz que haya un motor instalado.")
MSG_NO_ENGLISH = ("Tu teléfono no tiene la voz en inglés. Ve a Ajustes > Idioma > "
                  "Texto a voz y descarga inglés (EE. UU.).")


def spoken_text(category, passage):
    """Líneas que se leen en voz alta: sin 'A:'/'B:' ni 'Modelo:'."""
    text = passage or ""
    if category == "Speaking" and ":" in text:
        head, tail = text.split(":", 1)
        if head.strip().lower() in ("modelo", "model"):
            text = tail
    text = re.sub(r"(?:(?<=\s)|^)[AB]:\s*", "\n", text)
    text = text.replace("...", ", ")
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


class Speaker:
    """Texto a voz. En Android usa TextToSpeech; en escritorio, la voz del sistema."""

    def __init__(self):
        self.error = ""
        self._engine = None
        self._ready = False
        self._proc = None
        if platform == "android":
            self._init_android()

    # --- Android
    def _init_android(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method

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
            self._listener = InitListener(self._on_init)  # guardar la referencia
            self._engine = self._tts_cls(activity, self._listener)
        except Exception:
            self._engine = None
            self.error = MSG_NO_ENGINE

    def _on_init(self, status):
        if status != self._tts_cls.SUCCESS:
            self._engine = None
            self.error = MSG_NO_ENGINE
            return
        if self._engine.setLanguage(self._locale.US) < 0:  # -1 faltan datos, -2 sin soporte
            self.error = MSG_NO_ENGLISH
        self._ready = True

    def _speak_android(self, lines, slow):
        engine, cls = self._engine, self._tts_cls
        engine.setSpeechRate(0.6 if slow else 0.95)
        for i, line in enumerate(lines):
            engine.speak(line, cls.QUEUE_FLUSH if i == 0 else cls.QUEUE_ADD, None, None)
            engine.playSilentUtterance(450, cls.QUEUE_ADD, None)  # pausa entre frases

    # --- Escritorio (para probar en el computador)
    def _speak_desktop(self, lines, slow):
        import shutil
        import subprocess
        text = ". ".join(lines)
        kwargs = {"env": dict(os.environ, QUIZ_TEXT=text),
                  "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if platform == "win":
            script = ("Add-Type -AssemblyName System.Speech;"
                      "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                      "try { $s.SelectVoiceByHints('NotSet','NotSet',0,"
                      "[System.Globalization.CultureInfo]'en-US') } catch {};"
                      "$s.Rate = %d; $s.Speak($env:QUIZ_TEXT)" % (-3 if slow else 0))
            cmd = ["powershell", "-NoProfile", "-Command", script]
            kwargs["creationflags"] = 0x08000000  # sin ventana de consola
        elif platform == "macosx":
            cmd = ["say", "-v", "Samantha", "-r", "120" if slow else "180", text]
        else:
            exe = shutil.which("espeak-ng") or shutil.which("espeak")
            if exe:
                cmd = [exe, "-v", "en-us", "-s", "115" if slow else "150", text]
            elif shutil.which("spd-say"):
                cmd = ["spd-say", "-l", "en", "-r", "-40" if slow else "0", text]
            else:
                return "En este computador no hay voz instalada (instala espeak-ng o prueba en el celular)."
        try:
            self._proc = subprocess.Popen(cmd, **kwargs)
        except Exception:
            return "No se pudo iniciar la voz de este computador."
        return ""

    # --- API pública
    def speak(self, lines, slow=False):
        """Lee las líneas. Devuelve '' si todo va bien, o un mensaje para mostrar."""
        self.stop()
        if not lines:
            return "Este ejercicio no tiene texto para leer."
        if platform != "android":
            return self._speak_desktop(lines, slow)
        if self._engine is None:
            return self.error or MSG_NO_ENGINE
        if not self._ready:
            return "La voz se está iniciando. Toca de nuevo en un segundo."
        if self.error:
            return self.error
        try:
            self._speak_android(lines, slow)
        except Exception:
            return MSG_NO_ENGINE
        return ""

    def stop(self):
        if self._engine is not None and self._ready:
            try:
                self._engine.stop()
            except Exception:
                pass
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self._proc = None

    def shutdown(self):
        self.stop()
        if self._engine is not None:
            try:
                self._engine.shutdown()
            except Exception:
                pass


class MainScreen(Screen):
    def on_pre_enter(self, *args):
        """Resumen de progreso en la parte superior del inicio."""
        data = App.get_running_app().db.stats()
        total = sum(t for t, _ in data.values())
        good = sum(g for _, g in data.values())
        pct = int(round(100.0 * good / total)) if total else 0
        self.ids.home_pct.text = "%d%%" % pct
        self.ids.home_detail.text = (
            "%d de %d respuestas correctas" % (good, total) if total
            else "Aún sin resultados. ¡Empieza con cualquier área!")
        self.ids.home_bar.maximum = 100
        Animation(value=pct, d=0.4, t="out_quad").start(self.ids.home_bar)

    def open_area(self, category):
        self.manager.get_screen("area").set_category(category)
        self.go("area")

    def go(self, name):
        self.manager.transition.direction = "left"
        self.manager.current = name


class AreaScreen(Screen):
    category = ""
    exercises = []
    topic_map = {}
    index = 0
    first_try = True
    revealed = False
    correct_count = 0
    sound = None

    # --- configuración
    def set_category(self, category):
        self.category = category
        ids = self.ids
        ids.area_title.text = category
        ids.instruction.text = DESCRIPTIONS.get(category, "")
        rows = App.get_running_app().db.topics(category)
        self.topic_map = {r["name"]: r["id"] for r in rows}
        self.exercises = []
        self.index = 0
        self.correct_count = 0
        self.reset_display()
        show_audio = category in ("Listening", "Speaking")
        ids.audio_button.text = "Play audio" if category == "Listening" else "Listen to the model"
        ids.audio_row.disabled = not show_audio
        ids.audio_row.opacity = 1 if show_audio else 0
        ids.audio_row.height = dp(50) if show_audio else 0
        # El color del área tiñe la barra de avance y el botón principal
        accent = list(AREA_COLORS.get(category, PRIMARY))
        ids.bar.fill = accent
        ids.check_btn.bg = accent
        ids.topic_spinner.values = list(self.topic_map)
        ids.topic_spinner.text = "Select a topic"  # fuerza on_text al elegir el primero
        if self.topic_map:
            ids.topic_spinner.text = next(iter(self.topic_map))
        else:
            ids.topic_spinner.text = "No topics yet"

    def reset_display(self):
        ids = self.ids
        ids.prompt.text = "Elige un tema para empezar."
        ids.passage.text = ""
        ids.answer.text = ""
        self.clear_feedback()
        ids.progress.text = ""
        ids.bar.value = 0

    # --- flujo de ejercicios
    def load_topic(self, name):
        if name not in self.topic_map:
            return
        self.stop_audio()
        self.exercises = App.get_running_app().db.exercises(self.topic_map[name])
        self.index = 0
        self.correct_count = 0
        self.show_exercise()

    @property
    def current(self):
        return self.exercises[self.index] if self.exercises else None

    def show_exercise(self):
        ids = self.ids
        item = self.current
        if item is None:
            ids.prompt.text = "Este tema aún no tiene ejercicios. Añádelos en Manage topics."
            ids.passage.text = ""
            ids.progress.text = ""
            ids.bar.value = 0
            return
        self.first_try = True
        self.revealed = False
        ids.prompt.text = item["prompt"]
        # En Listening el texto nunca se muestra: solo se escucha.
        ids.passage.text = "" if self.category == "Listening" else item["passage"]
        ids.answer.text = ""
        self.clear_feedback()
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
            App.get_running_app().db.record_attempt(item["id"], ok)
            if ok:
                self.correct_count += 1
                self.ids.progress.text = "Ejercicio %d de %d  •  Aciertos: %d" % (
                    self.index + 1, len(self.exercises), self.correct_count)
            self.first_try = False
        if ok:
            self.set_feedback("¡Muy bien! Respuesta correcta.", OK_COLOR)
        else:
            self.set_feedback("Sigue practicando. Inténtalo de nuevo o pulsa 'Show answer'.",
                              BAD_COLOR)

    def show_answer(self):
        item = self.current
        if item is None:
            return
        if self.first_try:  # ver la respuesta sin intentarlo cuenta como fallo
            App.get_running_app().db.record_attempt(item["id"], False)
            self.first_try = False
        self.revealed = True
        options = alternatives(item["answer"])
        self.set_feedback("Respuesta esperada: " + " / ".join(options), INFO_COLOR)

    def next_exercise(self):
        if not self.exercises:
            return
        self.stop_audio()
        if self.index + 1 >= len(self.exercises):
            total = len(self.exercises)
            self.set_feedback("¡Tema completado! Aciertos: %d de %d. Volvemos al inicio del tema."
                              % (self.correct_count, total), OK_COLOR)
            self.index = 0
            self.correct_count = 0
            self.ids.answer.text = ""
            self.first_try = True
            self.ids.progress.text = "Tema completado"
            return
        self.index += 1
        self.show_exercise()

    def set_feedback(self, text, color):
        fb = self.ids.feedback
        fb.text = text
        fb.color = color
        fb.bg = (color[0], color[1], color[2], 0.16)

    def clear_feedback(self):
        fb = self.ids.feedback
        fb.text = ""
        fb.bg = (0, 0, 0, 0)

    # --- audio
    def stop_audio(self):
        App.get_running_app().speaker.stop()
        if self.sound:
            try:
                self.sound.stop()
            except Exception:
                pass
            self.sound = None

    def play_audio(self, slow=False):
        """Lee el texto del ejercicio en voz alta (sin mostrarlo en Listening)."""
        item = self.current
        if item is None:
            return
        self.stop_audio()
        # Si alguien dejó un MP3 con ese nombre se usa, pero no es necesario.
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

    def go_home(self):
        self.stop_audio()
        self.manager.transition.direction = "right"
        self.manager.current = "home"

    def on_leave(self, *args):
        self.stop_audio()


class StatsScreen(Screen):
    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        data = App.get_running_app().db.stats()
        box = self.ids.stats_box
        box.clear_widgets()
        total_all = sum(t for t, _ in data.values())
        good_all = sum(g for _, g in data.values())
        pct_all = int(round(100.0 * good_all / total_all)) if total_all else 0
        hero = StatHero(pct="%d%%" % pct_all)
        hero.detail = ("%d de %d respuestas correctas" % (good_all, total_all) if total_all
                       else "Responde algunos ejercicios para ver tu progreso.")
        box.add_widget(hero)
        for cat in CATEGORIES:
            total, good = data.get(cat, (0, 0))
            pct = int(round(100.0 * good / total)) if total else 0
            box.add_widget(StatRow(
                title=cat,
                detail="%d/%d  •  %d%%" % (good, total, pct),
                value=pct,
                fill=list(AREA_COLORS[cat])))

    def confirm_reset(self):
        confirm("Reset progress", "¿Borrar todo tu progreso?", self.do_reset)

    def do_reset(self):
        App.get_running_app().db.reset_progress()
        self.refresh()


class AdminScreen(Screen):
    topic_map = {}

    def on_pre_enter(self, *args):
        self.refresh_topics()

    def say(self, text, ok=True):
        color = OK_COLOR if ok else BAD_COLOR
        self.ids.status.text = text
        self.ids.status.color = color
        self.ids.status.bg = (color[0], color[1], color[2], 0.16)

    def refresh_topics(self):
        if "category" not in self.ids:
            return
        rows = App.get_running_app().db.topics(self.ids.category.text)
        self.topic_map = {r["name"]: r["id"] for r in rows}
        self.ids.topic_pick.values = list(self.topic_map)
        self.ids.topic_pick.text = next(iter(self.topic_map), "Select a topic")

    def save_topic(self):
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
        self.say("Tema guardado. Ahora puedes añadirle ejercicios.")

    def save_exercise(self):
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
        App.get_running_app().db.add_exercise(
            topic_id, prompt, ids.ex_passage.text.strip(), answer, "", ids.ex_mode.text)
        self.say("Ejercicio guardado correctamente.")
        for field in (ids.ex_prompt, ids.ex_passage, ids.ex_answer):
            field.text = ""

    def confirm_delete_topic(self):
        name = self.ids.topic_pick.text
        if name not in self.topic_map:
            self.say("Elige el tema que quieres eliminar.", False)
            return
        confirm("Delete topic",
                "¿Eliminar '%s' y todos sus ejercicios?" % name,
                lambda: self.delete_topic(name))

    def delete_topic(self, name):
        App.get_running_app().db.delete_topic(self.topic_map[name])
        self.refresh_topics()
        self.say("Tema eliminado.")


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
class EnglishQuizApp(App):
    def build(self):
        self.title = "English Quiz"
        # user_data_dir es escribible en Android/iOS y en escritorio
        os.makedirs(self.user_data_dir, exist_ok=True)
        self.db = Database(os.path.join(self.user_data_dir, DB_NAME))
        self.speaker = Speaker()  # se crea al inicio para que la voz esté lista al usarla
        Builder.load_string(KV)
        sm = ScreenManager(transition=SlideTransition(duration=0.2))
        sm.add_widget(MainScreen(name="home"))
        sm.add_widget(AreaScreen(name="area"))
        sm.add_widget(StatsScreen(name="stats"))
        sm.add_widget(AdminScreen(name="admin"))
        return sm

    def on_start(self):
        # Android: botón/gesto "atrás" vuelve al inicio en lugar de cerrar la app
        Window.bind(on_keyboard=self.on_back)

    def on_back(self, window, key, *args):
        if key == 27 and self.root.current != "home":
            self.root.transition.direction = "right"
            self.root.current = "home"
            return True
        return False

    def on_stop(self):
        self.speaker.shutdown()
        self.db.conn.close()


if __name__ == "__main__":
    EnglishQuizApp().run()