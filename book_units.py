"""Contenido completo y limpio basado en Top Notch Fundamentals A (Units 1 - 7).

Formato de cada ejercicio:
    (prompt, passage, answer, audio_file, mode, image_file)
- Si no hay imagen, image_file va vacío (""). Si pones un archivo en assets/images/,
  por ejemplo "u1_occupations.png", se mostrará automáticamente en pantalla.
- En 'answer', las respuestas válidas alternativas se separan con "|".
"""


def E(prompt, passage, answer, mode="exact", image=""):
    return (prompt, passage, answer, "", mode, image)


def L(prompt, audio_text, answer, image=""):
    return (prompt, audio_text, answer, "", "exact", image)


def S(prompt, model, answer, image=""):
    return (prompt + " Then type what you said.", "Modelo: " + model, answer, "", "contains", image)


def W(prompt, hint, answer, image=""):
    return (prompt, "Ejemplo / Regla: " + hint, answer, "", "exact", image)


def T(name, desc, rows):
    return (name, desc, rows)


# ==========================================================================
# READING (Unidades 1 a 7)
# ==========================================================================
READING = [
    T("Unit 1 - Names and Occupations", "Lee perfiles y tarjetas de presentación.", [
        E("What is John's occupation?",
          "Business Card: John Porter | Pilot | Licensed & Insured | john@airtaxi.com",
          "pilot|a pilot|he is a pilot|he's a pilot", image="u1_john_card.png"),
        E("Is Orlando Bloom a singer?",
          "Orlando Bloom is a famous actor. He is not a singer. Marta is an athlete.",
          "no|no he is not|no he's not|no he isn't"),
        E("What are Casey Affleck's three occupations?",
          "Casey Affleck is a famous actor. He's also a writer. And he's a director, too.",
          "actor writer and director|actor, writer, and director|actor writer director", mode="contains"),
    ]),
    T("Unit 2 - About People", "Lee información personal y de contacto.", [
        E("Where is Nadia Santini from?",
          "This is Nadia Santini. She's from Italy. Her occupation is chef.",
          "italy|she is from italy|she's from italy"),
        E("What is Vincent Lam's occupation?",
          "Vincent Lam is from Canada. Mr. Lam has two occupations. He's a doctor and a writer.",
          "doctor and writer|a doctor and a writer|doctor and a writer", mode="contains"),
        E("What is Lisa Kim's phone number?",
          "Contact Card: Lisa Kim | Phone: 25-61-0078 | E-mail: lisa.kim@hipnet.com",
          "25-61-0078|25610078"),
    ]),
    T("Unit 3 - Places and Transportation", "Lee sobre ubicaciones y cómo viajar.", [
        E("Where is the pharmacy?",
          "Maria lives in a small neighborhood. The pharmacy is across the street from the school. The bank is next to the pharmacy.",
          "across the street|across the street from the school|it's across the street", image="u3_map.png"),
        E("How does Laura Blake go to work?",
          "I'm Laura Blake. I go to work by car with my neighbor Brad Lane. Min Park goes to work by train.",
          "by car|car|she goes by car"),
        E("How does Matt Carson go to school?",
          "My school is right around the corner from my home, so I walk to school with my friends.",
          "walk|walks|he walks|on foot"),
    ]),
    T("Unit 4 - Family", "Lee sobre familias y descripciones.", [
        E("How many brothers and sisters does Gael García Bernal have?",
          "Gael García Bernal is a famous actor from Mexico. He has one sister and two brothers.",
          "one sister and two brothers|1 sister and 2 brothers|three|3", mode="contains"),
        E("What is Jay Chou's occupation?",
          "Meet Jay Chou, a famous singer from Taiwan. He is also an excellent musician and an actor.",
          "singer|singer musician and actor", mode="contains"),
        E("How old is Laura's brother?",
          "My name is Laura. I have one brother and two sisters. My brother is 20 years old. My sisters are 15 and 12.",
          "20|twenty|20 years old|he is 20|he's 20"),
    ]),
    T("Unit 5 - Events and Times", "Lee anuncios de eventos y horarios.", [
        E("What time is Sally Neufield's birthday party?",
          "PARTY: Sally Neufield's birthday! When: Tuesday, June 21st, 7:00 P.M. Where: Chuck's Café.",
          "7:00|7:00 pm|7:00 p.m.|at 7:00|seven o'clock"),
        E("When is the movie 'The Party'?",
          "MOVIE: English actor Peter Sellers in The Party. Friday, June 24th at 8:30 P.M. At the New School.",
          "friday june 24th at 8:30|friday|friday at 8:30", mode="contains"),
        E("Where is the volleyball game?",
          "GAME: Volleyball! Sunday, June 26th, 2:00 P.M. Branfield School on Fitch Avenue.",
          "branfield school|at branfield school"),
    ]),
    T("Unit 6 - Clothes", "Lee un anuncio de tienda de ropa.", [
        E("Until what time are Smith and Company stores open?",
          "Smith and Company: 1/2 Price Sale! Men's and Women's Clothes. All stores open until midnight.",
          "midnight|until midnight|12:00 am"),
        E("Where are blue sweaters available?",
          "Sale items: Sweaters, blouses, and shoes. Blue sweaters available at Main Street store only.",
          "main street|main street store|at main street"),
        E("What other sale items are available today?",
          "Other sale items today: Children's jackets and shoes. Locations: Main Street and Uptown Mall.",
          "children's jackets and shoes|jackets and shoes", mode="contains"),
    ]),
    T("Unit 7 - Activities", "Lee sobre rutinas y robots domésticos.", [
        E("What does the iRobot Roomba do?",
          "The iRobot Roomba turns right or left, and vacuums while you watch TV or exercise.",
          "vacuums|it vacuums"),
        E("What does the iRobot Scooba do?",
          "If you want to wash the floor, the iRobot Scooba washes the floor for you.",
          "washes the floor|washes floors|it washes the floor"),
        E("Can ASIMO climb stairs?",
          "Meet ASIMO, a robot from Honda. ASIMO walks, climbs stairs, carries things, and greets people.",
          "yes|yes it can|yes he can"),
    ]),
]

# ==========================================================================
# LISTENING (Unidades 1 a 7 - se lee con TTS y el texto permanece oculto)
# ==========================================================================
LISTENING = [
    T("Unit 1 - Spelling & Occupations", "Escucha el deletreo y la ocupación.", [
        L("Listen and write the last name you hear spelled.",
          "Hello. I'm John Bello. B, E, L, L, O.", "bello"),
        L("Listen and write the woman's occupation.",
          "A: Are you a flight attendant? B: No, I'm not. I'm a pilot.", "pilot|a pilot"),
        L("Listen and write the man's occupation.",
          "A: What do you do? B: I'm an architect.", "architect|an architect"),
    ]),
    T("Unit 2 - Contact Information", "Escucha nombres, números y correos.", [
        L("Listen and write the phone number.",
          "A: What's your phone number? B: 523-6620.", "523-6620|5236620|523 6620"),
        L("Listen and write where she is from.",
          "A: Where's she from? B: She's from Canada.", "canada|from canada"),
        L("Listen and write the street number.",
          "A: What's Ellen's address? B: 18 Main Street.", "18|eighteen|18 main street"),
    ]),
    T("Unit 3 - Directions & Transport", "Escucha direcciones y transporte.", [
        L("Listen and write where the bank is.",
          "A: Excuse me. Where's the bank? B: It's around the corner.", "around the corner"),
        L("Listen and write how B goes to school.",
          "A: How do you go to school? B: By subway. What about you? A: Me? I walk.", "by subway|subway"),
        L("Listen and write the negative imperative you hear.",
          "Can I walk to the school? Don't walk. Drive.", "don't walk|do not walk"),
    ]),
    T("Unit 4 - Family & Ages", "Escucha edades y parentescos.", [
        L("Listen and write the brother's age (in digits).",
          "A: How old is your brother? B: He's twenty.", "20|twenty"),
        L("Listen and write the sister's age (in digits).",
          "A: And your sisters? B: Eighteen and twenty-two.", "18|eighteen", mode="contains") if False else
        L("Listen and write the first age you hear (in digits).",
          "My sister is eighteen years old.", "18|eighteen"),
        L("Listen and write the adjective that describes her father.",
          "Tell me about your father. Well, he's a doctor. And he's very tall.", "tall|very tall"),
    ]),
    T("Unit 5 - Times & Birthdays", "Escucha la hora y fechas.", [
        L("Listen and write the time of the meeting (in digits, e.g. 10:00).",
          "A: What time is the meeting? B: Ten o'clock.", "10:00|10|ten o'clock"),
        L("Listen and write the day of the dance.",
          "Look. There's a dance on Wednesday at 10:30.", "wednesday"),
        L("Listen and write the month of A's birthday.",
          "A: When's your birthday? B: On July 15th. A: My birthday's in November.", "november"),
    ]),
    T("Unit 6 - Clothes, Colors & Sizes", "Escucha prendas, colores y tallas.", [
        L("Listen and write the color of the sweater.",
          "A: Do you have this sweater in green? B: Yes, we do.", "green"),
        L("Listen and write the size the husband needs.",
          "My husband needs a shirt. Do you have that shirt in large?", "large|l"),
        L("Listen and write the problem with the jacket.",
          "What do you think of this jacket? Well, it's nice, but it's a little tight.", "tight|a little tight"),
    ]),
    T("Unit 7 - Daily Routines & Chores", "Escucha horarios y tareas del hogar.", [
        L("Listen and write what time B gets up.",
          "I'm definitely an evening person. I get up after ten in the morning.", "10|10:00|after ten|after 10"),
        L("Listen and write how often B does the laundry.",
          "A: So how often do you do the laundry? B: About twice a week.", "twice a week"),
        L("Listen and write who cleans the house.",
          "A: Who cleans the house? B: Oh, that's my brother's job.", "brother|my brother|his brother"),
    ]),
]

# ==========================================================================
# SPEAKING (Unidades 1 a 7 - escucha el modelo, dilo y escríbelo)
# ==========================================================================
SPEAKING = [
    T("Unit 1 - Occupations & Spelling", "Preséntate y di tu ocupación.", [
        S("Say what you do using 'I'm a' or 'I'm an'.", "I'm an architect. And you?", "i'm|i am"),
        S("Ask someone how to spell their name.", "How do you spell that?", "how do you spell"),
    ]),
    T("Unit 2 - Introductions & Contact", "Presenta a un amigo y pide su número.", [
        S("Introduce your classmate Paula to Tom.", "Tom, this is Paula. Paula's my classmate.", "this is"),
        S("Ask for someone's phone number.", "What's your phone number?", "phone number"),
    ]),
    T("Unit 3 - Locations & Transport", "Pregunta por lugares y transporte.", [
        S("Ask where the bank is.", "Excuse me. Where's the bank?", "where's|where is"),
        S("Say how you go to school or work.", "I go to school by subway.", "by|walk|on foot"),
    ]),
    T("Unit 4 - Family Descriptions", "Habla de tu familia.", [
        S("Say how many brothers or sisters you have.", "I have one brother and two sisters.", "i have"),
        S("Describe a relative using 'very' or 'so'.", "My mother is very tall and pretty.", "very|so"),
    ]),
    T("Unit 5 - Time & Birthdays", "Confirma la hora y pregunta cumpleaños.", [
        S("Ask if you are late.", "Uh-oh. Am I late?", "am i late"),
        S("Say when your birthday is.", "My birthday is in November.", "birthday"),
    ]),
    T("Unit 6 - Compliments & Shopping", "Haz un cumplido y pide una talla.", [
        S("Compliment someone's dress or shoes.", "I really like that dress.", "like"),
        S("Ask if they have a sweater in green.", "Do you have this sweater in green?", "do you have"),
    ]),
    T("Unit 7 - Routines & Chores", "Habla de tu rutina y tareas.", [
        S("Say what you usually do in your free time.", "I usually read or watch TV.", "usually|sometimes|always"),
        S("Ask who washes the dishes in your family.", "Who washes the dishes in your family?", "who"),
    ]),
]

# ==========================================================================
# WRITING (Unidades 1 a 7 - gramática con explicación y ejemplo)
# ==========================================================================
WRITING = [
    T("Unit 1 - Articles a/an & Verb be", "Regla: usa 'an' antes de sonido vocal (an actor) y 'a' antes de consonante (a teacher).", [
        W("Complete: I'm ____ architect.", "Usa 'an' porque architect empieza con vocal.", "an"),
        W("Complete: She's not ____ banker.", "Usa 'a' antes de sonido consonante.", "a"),
        W("Complete with contraction: They ____ writers. (They are)", "Forma corta: They're", "they're"),
        W("Capitalize the proper noun: 'canada' -> ____", "Los países y nombres propios empiezan con mayúscula.", "Canada"),
    ]),
    T("Unit 2 - Possessives & Be from", "Regla: my, your, his, her, our, their. Contracción: Where is = Where's.", [
        W("Complete: Ms. Ellis is Joe's teacher. Joe is ____ student.", "Posesivo para 'she' (Ms. Ellis).", "her"),
        W("Complete: We are Sara and Todd's neighbors. We are ____ neighbors.", "Posesivo para 'they'.", "their"),
        W("Complete: ____ she from? She's from Japan.", "Contracción de 'Where is'.", "where's|where is"),
    ]),
    T("Unit 3 - Imperatives & By + Transport", "Regla: Imperativo negativo usa Don't + verbo. Transporte usa 'by' (excepto 'on foot').", [
        W("Make it negative: ____ drive to the bank.", "Usa Don't.", "don't|do not"),
        W("Complete: I go to work ____ bus.", "Preposición para medios de transporte.", "by"),
        W("Complete: She goes to school ____ foot.", "Excepción: no se usa 'by'.", "on"),
    ]),
    T("Unit 4 - Who, Have/Has & How old", "Regla: have (I/you/we/they), has (he/she/it). Edad: How old is/are...", [
        W("Complete: ____ is he? He's my grandfather.", "Pregunta por identidad de persona.", "who"),
        W("Complete: She ____ three sisters.", "Tercera persona singular: has.", "has"),
        W("Complete: How ____ are your parents? They're fifty.", "Pregunta por edad.", "old"),
    ]),
    T("Unit 5 - Prepositions in, on, at", "Regla: 'in' + mes (in May), 'on' + día/fecha (on Monday, on July 15th), 'at' + hora (at 8:30, at noon).", [
        W("Complete: The party is ____ Saturday.", "Con días de la semana se usa 'on'.", "on"),
        W("Complete: The movie is ____ 8:30 P.M.", "Con horas exactas se usa 'at'.", "at"),
        W("Complete: My birthday is ____ January.", "Con meses solos se usa 'in'.", "in"),
        W("Write 1:30 in words: It's ____ past one.", "Media hora después de la una.", "half"),
    ]),
    T("Unit 6 - Demonstratives & Simple Present", "Regla: this/that (singular), these/those (plural). Adjetivo va ANTES del sustantivo (a long skirt).", [
        W("Complete: I like ____ shoes. (plural, cerca)", "Plural cercano: these.", "these"),
        W("Complete: He ____ a new suit. (need)", "En presente simple con he/she/it agrega -s.", "needs"),
        W("Complete: She ____ like red shirts. (negative)", "Negativo para she: doesn't.", "doesn't|does not"),
        W("Complete: Which sweater do you want? The blue ____.", "Reemplaza un sustantivo singular.", "one"),
    ]),
    T("Unit 7 - Frequency Adverbs & Present Simple", "Regla: El adverbio (always, usually, sometimes, never) va ANTES del verbo principal.", [
        W("Write third-person singular of 'watch': He ____ TV.", "Termina en -ch, agrega -es.", "watches"),
        W("Write third-person singular of 'study': She ____ English.", "Consonante + y cambia a -ies.", "studies"),
        W("Complete: ____ washes the dishes in your family?", "Pregunta por el sujeto que hace la acción.", "who"),
        W("Complete: I go shopping ____ a week. (2 times)", "Dos veces = twice.", "twice"),
    ]),
]

# ==========================================================================
# CONVERSATIONS (Unidades 1 a 7 - modelos reales del libro)
# ==========================================================================
CONVERSATIONS = [
    T("Unit 1 - Meeting Classmates", "Saluda y pregunta ocupaciones.", [
        E("A: What do you do?  B: I'm an architect. And ____?",
          "Estrategia: Usa 'And you?' para devolver la pregunta.", "you"),
        E("A: Excuse me. Are you Marie?  B: No, I'm ____. I'm Laura.",
          "Respuesta corta negativa.", "not"),
    ]),
    T("Unit 2 - Introducing Friends", "Presenta a alguien y pide datos.", [
        E("A: Tom, ____ is Paula. Paula's my classmate.  B: Hi, Paula.",
          "Usa 'this is' para presentar personas.", "this"),
        E("A: What's your ____ name, please?  B: Fava.  A: And your first name?  B: Bob.",
          "Apellido = last name.", "last"),
    ]),
    T("Unit 3 - Asking Directions", "Pide indicaciones en la ciudad.", [
        E("A: Can I walk to the bookstore?  B: Sure.  A: And what ____ the school?  B: Don't walk. Drive.",
          "Usa 'what about' para preguntar por otra opción.", "about"),
        E("A: Thanks!  B: You're ____.",
          "Respuesta cortés a 'Thanks'.", "welcome"),
    ]),
    T("Unit 4 - Talking About Family", "Conversa sobre tus familiares.", [
        E("A: Tell me ____ your father.  B: Well, he's a doctor and he's very tall.",
          "Usa 'Tell me about...' para pedir que hablen de un tema.", "about"),
        E("A: I have one brother.  B: ____? How old is he?",
          "Usa 'Really?' para mostrar interés.", "really"),
    ]),
    T("Unit 5 - Making Plans & Events", "Confirma la hora e invita a un evento.", [
        E("A: What time is the meeting?  B: 10:00.  A: Uh-oh. Am I ____?  B: No, you're early.",
          "Tarde = late.", "late"),
        E("A: Look. There's a dance on Wednesday.  B: ____! What time?",
          "Muestra entusiasmo con 'Great!'.", "great"),
    ]),
    T("Unit 6 - Shopping for Clothes", "Elogia ropa y pregunta tallas.", [
        E("A: I really ____ that dress.  B: Thank you!",
          "Verbo gustar = like.", "like"),
        E("A: Do you have that shirt in large?  B: No, I'm sorry. We don't.  A: That's too ____.",
          "Expresa decepción con 'That's too bad.'", "bad"),
    ]),
    T("Unit 7 - Daily Life & Chores", "Habla de tu día típico.", [
        E("A: Are you a morning person or an ____ person?  B: I'm definitely an evening person.",
          "Opuesto de morning = evening.", "evening"),
        E("A: How ____ do you do the laundry?  B: About twice a week.",
          "Pregunta frecuencia con 'How often'.", "often"),
    ]),
]

BOOK_UNITS = {
    "Reading": READING,
    "Listening": LISTENING,
    "Speaking": SPEAKING,
    "Writing": WRITING,
    "Conversations": CONVERSATIONS,
}