"""Ejercicios adicionales de Review - Units 3 & 4 (25 por apartado en cada unidad).

Mismo formato que SEED en main.py:
    categoría -> [(tema, descripción, [(pregunta, texto, respuesta, audio, modo), ...]), ...]
- En la respuesta se separan las alternativas válidas con "|".
- Listening: el campo 'texto' es lo que se LEE EN VOZ ALTA y nunca se muestra.
- Speaking: modo 'contains' (basta con que la respuesta incluya la frase clave).
"""


def E(prompt, passage, answer, mode="exact"):
    return (prompt, passage, answer, "", mode)


def L(prompt, audio, answer):          # Listening
    return E(prompt, audio, answer)


def S(prompt, model, answer):          # Speaking
    return E(prompt + " Then type what you said.", "Modelo: " + model, answer, "contains")


def W(prompt, hint, answer):           # Writing
    return E(prompt, "Pista: " + hint, answer)


def T(name, desc, rows):
    return (name, desc, rows)


# ==========================================================================
# READING
# ==========================================================================
R3_1 = ("Maria lives in a small neighborhood. The pharmacy is across the street from the "
        "school. The bank is next to the pharmacy. The restaurant is around the corner.")
R3_2 = ("Tom lives down the street from the bookstore. He goes to school by bus. His sister "
        "goes to the bank on foot. His mom drives to the pharmacy.")
R3_3 = ("This is a map in words. The school is on the left. The bookstore is on the right. "
        "The newsstand is between the school and the bookstore.")
R3_4 = ("A: How do I get to the bank?\nB: Walk down the street. The bank is on the right. "
        "Don't take the bus.")
R3_5 = ("Ana takes the train to work. Her brother takes a taxi to school. Her dad drives to "
        "the restaurant. Her mom takes the subway.")
R3_6 = ("A newsstand is where you buy newspapers and magazines. A restaurant is where you eat "
        "food. A school is where you study and learn.")

R4_1 = ("My name is Laura. I have one brother and two sisters. My brother is 20 years old. "
        "My sisters are 15 and 12.")
R4_2 = "This is Peter. He's tall and handsome. He's 30 years old. He has a son and a daughter."
R4_3 = "My grandfather is 78 years old. He has three children. He has two sisters."
R4_4 = ("Anna is 19. She has five cousins. Her cousin Sofia is cute. Sofia is 8 years old.")
R4_5 = ("A: Who is he?\nB: He's my dad.\nA: How old is he?\nB: He's fifty.\n"
        "A: Who's Louise?\nB: She's my mom.")
R4_6 = ("I have two sisters. Their names are Ana and Eva. They're pretty. Ana is short and 17 "
        "years old. Eva is tall and 22 years old.")
R4_7 = ("My dad is tall. My mom is short. My brother is young. My grandfather is old. "
        "My sister is very pretty.")

READING = [
    # ---- Unit 3
    T("Unit 3 - Maria's neighborhood", "Dónde queda cada lugar.", [
        E("Where is the pharmacy?", R3_1,
          "across the street|across the street from the school|it's across the street|it is across the street"),
        E("Where is the bank?", R3_1,
          "next to the pharmacy|it's next to the pharmacy|it is next to the pharmacy"),
        E("Where is the restaurant?", R3_1,
          "around the corner|it's around the corner|it is around the corner"),
    ]),
    T("Unit 3 - Tom and his family", "Cómo se mueve cada persona.", [
        E("How does Tom go to school?", R3_2, "by bus|bus|on the bus|he goes by bus"),
        E("How does Tom's sister go to the bank?", R3_2,
          "on foot|she goes on foot|walks|she walks|walking"),
        E("How does Tom's mom go to the pharmacy?", R3_2,
          "drives|she drives|drive|by car|she goes by car"),
    ]),
    T("Unit 3 - A map in words", "Izquierda, derecha y entre.", [
        E("Where is the school?", R3_3, "on the left|it's on the left|it is on the left|left"),
        E("Where is the bookstore?", R3_3, "on the right|it's on the right|it is on the right|right"),
        E("What is between the school and the bookstore?", R3_3,
          "the newsstand|newsstand|a newsstand"),
    ]),
    T("Unit 3 - How do I get there?", "Lee unas direcciones.", [
        E("Where is the bank?", R3_4, "on the right|it's on the right|it is on the right|right"),
        E("How do you get to the bank?", R3_4,
          "walk|walk down the street|on foot|you walk"),
        E("What shouldn't you take?", R3_4, "the bus|bus|don't take the bus|take the bus"),
    ]),
    T("Unit 3 - Ana's family travels", "Medios de transporte.", [
        E("Who takes the train?", R3_5, "ana"),
        E("How does Ana's brother go to school?", R3_5,
          "takes a taxi|by taxi|taxi|a taxi|he takes a taxi"),
        E("Who takes the subway?", R3_5, "her mom|ana's mom|mom|her mother|ana's mother"),
    ]),
    T("Unit 3 - What is it?", "Qué se hace en cada lugar.", [
        E("Where do you eat food?", R3_6, "restaurant|a restaurant|at a restaurant|the restaurant"),
        E("Where do you buy newspapers?", R3_6, "newsstand|a newsstand|at a newsstand|the newsstand"),
        E("Where do you study and learn?", R3_6, "school|a school|at school|at a school|the school"),
    ]),
    # ---- Unit 4
    T("Unit 4 - Laura's family", "Hermanos y edades.", [
        E("How many brothers does Laura have?", R4_1, "one|1|one brother|she has one brother"),
        E("How many sisters does Laura have?", R4_1, "two|2|two sisters|she has two sisters"),
        E("How old is Laura's brother?", R4_1,
          "20|twenty|20 years old|twenty years old|he's 20|he's twenty"),
    ]),
    T("Unit 4 - Meet Peter", "Descripción de una persona.", [
        E("How old is Peter?", R4_2,
          "30|thirty|30 years old|thirty years old|he's 30|he's thirty"),
        E("Is Peter tall or short?", R4_2, "tall|he's tall|he is tall"),
        E("What children does Peter have?", R4_2,
          "a son and a daughter|son and daughter|one son and one daughter|a son and daughter"),
    ]),
    T("Unit 4 - The grandfather", "Abuelo, hijos y hermanas.", [
        E("How old is the grandfather?", R4_3,
          "78|seventy-eight|78 years old|seventy-eight years old|he's 78"),
        E("How many children does he have?", R4_3, "three|3|three children|he has three"),
        E("How many sisters does he have?", R4_3, "two|2|two sisters|he has two"),
    ]),
    T("Unit 4 - Anna and her cousins", "Primos y edades.", [
        E("How many cousins does Anna have?", R4_4, "five|5|five cousins|she has five"),
        E("Who is cute?", R4_4, "sofia|her cousin sofia|anna's cousin sofia"),
        E("How old is Sofia?", R4_4,
          "8|eight|8 years old|eight years old|she's 8|she's eight"),
    ]),
    T("Unit 4 - Who is he?", "Un diálogo sobre la familia.", [
        E("Who is he?", R4_5, "dad|my dad|he's my dad|he is my dad|father|my father"),
        E("How old is the dad?", R4_5,
          "50|fifty|50 years old|fifty years old|he's 50|he's fifty"),
        E("Who is Louise?", R4_5,
          "mom|my mom|she's my mom|she is my mom|mother|my mother"),
    ]),
    T("Unit 4 - Two sisters", "Ana y Eva.", [
        E("How many sisters does the speaker have?", R4_6, "two|2|two sisters"),
        E("Who is tall?", R4_6, "eva"),
        E("How old is Ana?", R4_6,
          "17|seventeen|17 years old|seventeen years old|she's 17|she's seventeen"),
    ]),
    T("Unit 4 - Describing the family", "Adjetivos para describir.", [
        E("Who is tall?", R4_7, "my dad|dad|the dad|father|my father"),
        E("Who is short?", R4_7, "my mom|mom|the mom|mother|my mother"),
        E("Who is old?", R4_7, "my grandfather|grandfather|the grandfather"),
    ]),
]

# ==========================================================================
# LISTENING  (el texto se lee en voz alta y no se muestra)
# ==========================================================================
LISTENING = [
    # ---- Unit 3
    T("Unit 3 - Where's the...? (1)", "Escucha dónde queda cada lugar.", [
        L("Listen and write the place they are asking about.",
          "A: Where's the newsstand? B: It's down the street.", "newsstand|the newsstand|a newsstand"),
        L("Listen and write where it is.",
          "A: Where's the newsstand? B: It's down the street.",
          "down the street|it's down the street|it is down the street"),
        L("Listen and write the place they are asking about.",
          "A: Where's the school? B: It's on the left.", "school|the school|a school"),
        L("Listen and write where it is.",
          "A: Where's the school? B: It's on the left.",
          "on the left|it's on the left|it is on the left|left"),
    ]),
    T("Unit 3 - Where's the...? (2)", "Escucha dónde queda cada lugar.", [
        L("Listen and write the place they are asking about.",
          "A: Where's the bookstore? B: It's between the bank and the restaurant.",
          "bookstore|the bookstore|a bookstore"),
        L("Listen and write where it is.",
          "A: Where's the bookstore? B: It's between the bank and the restaurant.",
          "between the bank and the restaurant|it's between the bank and the restaurant"),
        L("Listen and write the place they are asking about.",
          "A: Where's the bank? B: It's on the right.", "bank|the bank|a bank"),
        L("Listen and write where it is.",
          "A: Where's the bank? B: It's on the right.",
          "on the right|it's on the right|it is on the right|right"),
    ]),
    T("Unit 3 - Pharmacy and directions", "Lugares y cómo llegar.", [
        L("Listen and write the place they are asking about.",
          "A: Where's the pharmacy? B: It's next to the school.",
          "pharmacy|the pharmacy|a pharmacy"),
        L("Listen and write where it is.",
          "A: Where's the pharmacy? B: It's next to the school.",
          "next to the school|it's next to the school|it is next to the school"),
        L("Listen and write the verb.", "Walk to the bank.", "walk"),
        L("Listen and write the instruction you hear in the answer.",
          "A: How do I get to the bank? B: Walk across the street.",
          "walk across the street|walk across|walk"),
    ]),
    T("Unit 3 - Transportation (1)", "Cómo va cada persona.", [
        L("Listen and write the transportation.", "I go to school by bus.", "by bus|bus"),
        L("Listen and write the transportation.", "She goes to work by car.", "by car|car"),
        L("Listen and write how he goes there.", "He goes to the bank on foot.",
          "on foot|walking|he walks|walks"),
        L("Listen and write the transportation.", "We go to the restaurant by taxi.",
          "by taxi|taxi"),
    ]),
    T("Unit 3 - Transportation (2)", "Más medios de transporte.", [
        L("Listen and write the transportation.", "They go to the school by bicycle.",
          "by bicycle|bicycle|by bike|bike"),
        L("Listen and write the transportation.", "My brother goes to work by motorcycle.",
          "by motorcycle|motorcycle"),
        L("Listen and write how the person goes.", "I take the subway to the bookstore.",
          "the subway|subway|by subway|take the subway|takes the subway"),
    ]),
    # ---- Unit 4
    T("Unit 4 - How old? (1)", "Escucha las edades.", [
        L("Listen and write the age (in digits).",
          "A: How old is your brother? B: He's twenty-two.",
          "22|twenty-two|twenty two|he's 22|he's twenty-two"),
        L("Listen and write the age (in digits).",
          "A: How old is she? B: She's thirty-three.",
          "33|thirty-three|thirty three|she's 33|she's thirty-three"),
        L("Listen and write the age (in digits).",
          "A: How old are they? B: They're fifteen.", "15|fifteen|they're 15|they're fifteen"),
        L("Listen and write the age (in digits).",
          "A: How old is he? B: He's sixty.", "60|sixty|he's 60|he's sixty"),
    ]),
    T("Unit 4 - How old? (2)", "Escucha las edades.", [
        L("Listen and write the age (in digits).",
          "A: How old is your sister? B: She's twelve.", "12|twelve|she's 12|she's twelve"),
        L("Listen and write the age (in digits).", "My mom is forty-five years old.",
          "45|forty-five|forty five|45 years old|forty-five years old"),
        L("Listen and write the age (in digits).", "My grandfather is seventy years old.",
          "70|seventy|70 years old|seventy years old"),
        L("Listen and write the age (in digits).", "They're twenty.",
          "20|twenty|they're 20|they're twenty"),
    ]),
    T("Unit 4 - Who is...?", "Escucha quién es cada persona.", [
        L("Listen and write who she is.", "A: Who is she? B: She's my sister.",
          "sister|my sister|she's my sister|she is my sister"),
        L("Listen and write who he is.", "A: Who is he? B: He's my grandfather.",
          "grandfather|my grandfather|he's my grandfather|he is my grandfather"),
        L("Listen and write who they are.", "A: Who are they? B: They're my cousins.",
          "cousins|my cousins|they're my cousins|they are my cousins"),
        L("Listen and write who Peter is.", "A: Who's Peter? B: He's my brother.",
          "brother|my brother|he's my brother|he is my brother"),
        L("Listen and write who they are.", "A: Who are they? B: They're my sisters.",
          "sisters|my sisters|they're my sisters|they are my sisters"),
    ]),
    T("Unit 4 - Have / has", "Escucha quién tiene qué.", [
        L("Listen and write the family member.", "I have one brother.",
          "brother|a brother|one brother"),
        L("Listen and write how many sisters she has.", "She has two sisters.",
          "two|2|two sisters"),
        L("Listen and write the two family members.", "He has a son and a daughter.",
          "son and daughter|a son and a daughter|a son and daughter"),
        L("Listen and write how many cousins.", "We have three cousins.",
          "three|3|three cousins"),
        L("Listen and write how many siblings.", "My mom has two siblings.",
          "two|2|two siblings"),
    ]),
    T("Unit 4 - Describing people", "Escucha el adjetivo.", [
        L("Listen and write the adjective.", "My sister is very pretty.", "pretty|very pretty"),
        L("Listen and write the adjective.", "My dad is tall.", "tall"),
        L("Listen and write the adjective.", "My grandfather is old.", "old"),
        L("Listen and write the adjective.", "He's very handsome.", "handsome|very handsome"),
    ]),
]

# ==========================================================================
# SPEAKING
# ==========================================================================
SPEAKING = [
    # ---- Unit 3
    T("Unit 3 - Ask where places are", "Pregunta dónde queda cada lugar.", [
        S("Ask where the pharmacy is.", "Where's the pharmacy?", "where's the pharmacy|where is the pharmacy"),
        S("Ask where the restaurant is.", "Where's the restaurant?", "where's the restaurant|where is the restaurant"),
        S("Ask where the newsstand is.", "Where's the newsstand?", "where's the newsstand|where is the newsstand"),
        S("Ask where the bookstore is.", "Where's the bookstore?", "where's the bookstore|where is the bookstore"),
        S("Ask where the school is.", "Where's the school?", "where's the school|where is the school"),
    ]),
    T("Unit 3 - Say where it is (1)", "Responde con expresiones de lugar.", [
        S("Say where the restaurant is. Use 'across the street'.",
          "The restaurant is across the street.", "across the street"),
        S("Say where the newsstand is. Use 'down the street'.",
          "The newsstand is down the street.", "down the street"),
        S("Say where the school is. Use 'around the corner'.",
          "The school is around the corner.", "around the corner"),
    ]),
    T("Unit 3 - Say where it is (2)", "Izquierda, derecha y entre.", [
        S("Say where the bank is. Use 'on the left'.", "The bank is on the left.", "on the left"),
        S("Say where the pharmacy is. Use 'on the right'.",
          "The pharmacy is on the right.", "on the right"),
        S("Say where the bookstore is. Use 'between'.",
          "The bookstore is between the school and the bank.", "between"),
    ]),
    T("Unit 3 - Giving directions", "Imperativos para dar direcciones.", [
        S("Tell a friend to walk to the bank.", "Walk to the bank.", "walk"),
        S("Tell a friend to take the bus to the school.", "Take the bus to the school.",
          "take the bus"),
        S("Tell a friend not to drive.", "Don't drive.", "don't drive|do not drive"),
        S("Tell a friend not to take the subway.", "Don't take the subway.",
          "don't take the subway|do not take the subway"),
    ]),
    T("Unit 3 - How do you go? (2)", "Transporte con BY.", [
        S("Say how you go to school. Use 'by bus'.", "I go to school by bus.", "by bus"),
        S("Say how you go to work. Use 'by car'.", "I go to work by car.", "by car"),
        S("Say how you go to the bank. Use 'on foot'.", "I go to the bank on foot.", "on foot"),
        S("Say how you go to the restaurant. Use 'by taxi'.",
          "I go to the restaurant by taxi.", "by taxi"),
        S("Say how you go to the bookstore. Use 'by bicycle'.",
          "I go to the bookstore by bicycle.", "by bicycle|by bike"),
    ]),
    # ---- Unit 4
    T("Unit 4 - Who is...?", "Pregunta quién es cada persona.", [
        S("Ask who a man is.", "Who is he?", "who is he|who's he"),
        S("Ask who a woman is.", "Who is she?", "who is she|who's she"),
        S("Ask who two people are.", "Who are they?", "who are they"),
        S("Ask who Louise is.", "Who's Louise?", "who's louise|who is louise"),
    ]),
    T("Unit 4 - Ask about ages", "Pregunta la edad.", [
        S("Ask how old a man is.", "How old is he?", "how old is he"),
        S("Ask how old a girl is.", "How old is she?", "how old is she"),
        S("Ask how old two people are.", "How old are they?", "how old are they"),
    ]),
    T("Unit 4 - Say the age", "Responde con edades.", [
        S("Say your brother is twenty years old.", "He's twenty years old.",
          "he's twenty|he is twenty|he's 20"),
        S("Say your sister is eighteen.", "She's eighteen.",
          "she's eighteen|she is eighteen|she's 18"),
        S("Say two people are fifty.", "They're fifty.",
          "they're fifty|they are fifty|they're 50"),
        S("Say how old you are.", "I'm twenty-five years old.", "i'm|i am"),
    ]),
    T("Unit 4 - Introduce your family", "Presenta a tu familia.", [
        S("Say that a woman is your sister.", "She's my sister.",
          "she's my sister|she is my sister"),
        S("Say that a man is your grandfather.", "He's my grandfather.",
          "he's my grandfather|he is my grandfather"),
        S("Say that two people are your cousins.", "They're my cousins.",
          "they're my cousins|they are my cousins"),
        S("Say that Louise is your mom.", "She's my mom.", "she's my mom|she is my mom"),
    ]),
    T("Unit 4 - Have / has", "Habla de tu familia con have y has.", [
        S("Say you have a brother.", "I have a brother.", "i have a brother"),
        S("Say your sister has one brother.", "She has one brother.", "she has one brother"),
        S("Say your mom has three siblings.", "My mom has three siblings.",
          "has three siblings|has 3 siblings"),
        S("Say that your family has cousins.", "We have cousins.", "we have cousins"),
    ]),
    T("Unit 4 - Describe people", "Describe a tu familia.", [
        S("Describe your sister. Use 'pretty'.", "She's very pretty.", "pretty"),
        S("Describe your dad. Use 'tall'.", "He's tall.", "tall"),
        S("Describe your brother. Use 'handsome'.", "He's very handsome.", "handsome"),
    ]),
]

# ==========================================================================
# WRITING
# ==========================================================================
WRITING = [
    # ---- Unit 3
    T("Unit 3 - Places and Where's", "Preguntas y lugares.", [
        W("Complete: ____ the newsstand? (short form of Where is)", "Where's + the place.",
          "where's|where is"),
        W("Write the place: where you buy medicine (one word).", "Empieza con P.", "pharmacy"),
        W("Write the place: where you keep your money (one word).", "Empieza con B.", "bank"),
    ]),
    T("Unit 3 - Direction words (1)", "Palabras de dirección.", [
        W("Complete: Where's the school? It's ____ the bank. (beside)", "next to.", "next to"),
        W("Complete: The school is on the ____. (opposite of right)", "Left o right.", "left"),
        W("Complete: The bank is on the ____. (opposite of left)", "Left o right.", "right"),
    ]),
    T("Unit 3 - Direction words (2)", "Más palabras de dirección.", [
        W("Complete: It's ____ the street. (further along the same road)", "down the street.",
          "down"),
        W("Complete: The bookstore is ____ the school and the bank. (in the middle of two places)",
          "Significa 'entre'.", "between"),
        W("Complete: ____ a taxi to the restaurant.", "Imperativo: Take + transporte.", "take"),
    ]),
    T("Unit 3 - Imperatives (2)", "Dar instrucciones.", [
        W("Complete: ____ to the restaurant. (go by car)", "Verbo base, sin sujeto.", "drive"),
        W("Make it negative: ____ walk.", "Forma negativa del imperativo.", "don't|do not"),
        W("Make it negative: ____ take the subway.", "Forma negativa del imperativo.",
          "don't|do not"),
    ]),
    T("Unit 3 - BY + transportation (2)", "BY o 'on foot'.", [
        W("Complete: My dad goes to work ____ train.", "BY + vehículo.", "by"),
        W("Complete: We go to the restaurant ____ taxi.", "BY + vehículo.", "by"),
        W("Complete: I go to school ____ foot.", "Es la excepción: no se dice 'by foot'.", "on"),
    ]),
    # ---- Unit 4
    T("Unit 4 - Who and short forms", "Who y formas cortas.", [
        W("Complete: ____ is she? She's my sister.", "Pregunta por personas.", "who"),
        W("Complete: ____ are they? They're my cousins.", "Dos o más personas.", "who"),
        W("Complete: ____ my sister. (short form of She is)", "She + 's.", "she's"),
        W("Complete: ____ my grandfather. (short form of He is)", "He + 's.", "he's"),
    ]),
    T("Unit 4 - Have / has (2)", "have o has.", [
        W("Complete: He ____ two sisters.", "he, she, it usan has.", "has"),
        W("Complete: They ____ two children.", "they usa have.", "have"),
        W("Complete: You ____ a sister.", "you usa have.", "have"),
        W("Complete: My dad ____ one brother.", "my dad = he.", "has"),
    ]),
    T("Unit 4 - Opposites and ages", "Adjetivos y edades.", [
        W("Write the opposite of 'tall'.", "Describe la altura.", "short"),
        W("Write the opposite of 'young'.", "Describe la edad.", "old"),
        W("Complete: How ____ is he? He's twenty.", "Pregunta por la edad.", "old"),
    ]),
    T("Unit 4 - Numbers", "Números en letras.", [
        W("Write 20 in words.", "tw...", "twenty"),
        W("Write 50 in words.", "fif...", "fifty"),
    ]),
]

# ==========================================================================
# CONVERSATIONS
# ==========================================================================
CONVERSATIONS = [
    # ---- Unit 3
    T("Unit 3 - Where's the...? (1)", "Pregunta y responde dónde queda un lugar.", [
        E("A: Where's the bank?  B: It's ____ the street.", "Significa: al otro lado de la calle.",
          "across"),
        E("A: Where's the newsstand?  B: It's ____ the corner.", "Significa: hay que girar.",
          "around"),
        E("A: Where's the school?  B: It's on the ____.", "Es el lado contrario a 'right'.",
          "left"),
    ]),
    T("Unit 3 - Where's the...? (2)", "Más diálogos de ubicación.", [
        E("A: Where's the pharmacy?  B: It's on the ____.", "Es el lado contrario a 'left'.",
          "right"),
        E("A: Where's the bookstore?  B: It's ____ the bank and the school.",
          "Significa 'entre'.", "between"),
        E("A: ____ the restaurant?  B: It's down the street.", "Forma corta de Where is.",
          "where's|where is"),
    ]),
    T("Unit 3 - How do I get there?", "Dar direcciones.", [
        E("A: How do I get to the school?  B: ____ the bus.", "Imperativo: subir al bus.",
          "take"),
        E("A: How do I get to the bookstore?  B: ____ down the street.", "Imperativo: ir a pie.",
          "walk"),
        E("A: Should I drive to the bank?  B: No. ____ drive. Walk.",
          "Forma negativa del imperativo.", "don't|do not"),
    ]),
    T("Unit 3 - How do you go?", "Hablar del transporte.", [
        E("A: How do you go to work?  B: I go ____ train.", "BY + transporte.", "by"),
        E("A: How do you go to school?  B: I go ____ foot.", "Es la excepción: no se dice 'by foot'.",
          "on"),
        E("A: How does she go to the bank?  B: She goes ____ car.", "BY + transporte.", "by"),
    ]),
    T("Unit 3 - More transportation", "Más diálogos.", [
        E("A: How do they go to the restaurant?  B: They go ____ taxi.", "BY + transporte.", "by"),
        E("A: Do you drive to school?  B: No. I take the ____.",
          "Un transporte público: bus, train, subway...", "bus|train|subway|taxi"),
        E("A: Is the bank next to the school?  B: Yes, it's ____ to the school.",
          "Forma completa: next to.", "next"),
    ]),
    T("Unit 3 - Is it...?", "Confirmar ubicaciones.", [
        E("A: Excuse me. ____ is the bank?  B: It's across the street.",
          "Palabra para preguntar por lugares.", "where"),
        E("A: Is the pharmacy on the left?  B: No, it's on the ____.",
          "El lado contrario.", "right"),
        E("A: Where's the school?  B: It's ____ the bookstore. (beside)", "Dos palabras.",
          "next to"),
    ]),
    # ---- Unit 4
    T("Unit 4 - Who is she?", "Preguntar por personas.", [
        E("A: Who is she?  B: ____ my sister.", "Forma corta de She is.", "she's|she is"),
        E("A: Who are they?  B: They're my ____.", "Pista: primos.", "cousins"),
        E("A: ____ is he?  B: He's my grandfather.", "Palabra para preguntar por personas.",
          "who"),
    ]),
    T("Unit 4 - How old?", "Preguntar y decir la edad.", [
        E("A: How old is your brother?  B: ____ twenty.", "Forma corta de He is.", "he's|he is"),
        E("A: How old ____ they?  B: They're fifty.", "Dos o más personas.", "are"),
        E("A: How ____ is your sister?  B: She's 18.", "Pregunta por la edad.", "old"),
    ]),
    T("Unit 4 - Have / has (conversation)", "Diálogos con have y has.", [
        E("A: Do you have a brother?  B: Yes, I ____ one brother.", "I usa have.", "have"),
        E("A: Does he have sisters?  B: Yes, he ____ two sisters.", "he usa has.", "has"),
        E("A: Do they have children?  B: Yes, they ____ two children.", "they usa have.",
          "have"),
    ]),
    T("Unit 4 - Family members", "Quién es quién.", [
        E("A: Who's Louise?  B: She's my ____.", "Pista: la mamá.", "mom|mother"),
        E("A: Is he your dad?  B: No, he's my ____.", "Pista: el abuelo.", "grandfather"),
        E("A: Is she your sister?  B: Yes, ____ my sister.", "Forma corta de She is.",
          "she's|she is"),
    ]),
    T("Unit 4 - Describing people", "Describir a la familia.", [
        E("A: Is your dad tall?  B: Yes, he's very ____.", "Describe la altura.", "tall"),
        E("A: Is your sister short?  B: No, she's ____.", "Es lo contrario de short.", "tall"),
        E("A: Is your grandfather young?  B: No, he's ____.", "Es lo contrario de young.", "old"),
    ]),
    T("Unit 4 - Appearance", "Más descripciones.", [
        E("A: Is your brother handsome?  B: Yes, he's very ____.", "Describe a un hombre atractivo.",
          "handsome"),
        E("A: Is your sister pretty?  B: Yes, she's very ____.", "Describe a una mujer atractiva.",
          "pretty"),
        E("A: Does your mom have siblings?  B: Yes, she ____ three siblings.", "she usa has.",
          "has"),
    ]),
    T("Unit 4 - More family talk", "Últimos diálogos.", [
        E("A: How old is your cousin?  B: She's ____. (8)", "Escribe el número en letras o dígitos.",
          "eight|8"),
        E("A: Is he your brother?  B: Yes, ____ my brother.", "Forma corta de He is.",
          "he's|he is"),
        E("A: How many sisters do you have?  B: I ____ two sisters.", "I usa have.", "have"),
    ]),
]

EXTRA_UNITS_3_4 = {
    "Reading": READING,
    "Listening": LISTENING,
    "Speaking": SPEAKING,
    "Writing": WRITING,
    "Conversations": CONVERSATIONS,
}