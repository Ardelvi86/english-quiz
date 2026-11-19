import firebase_admin
from firebase_admin import auth, credentials

cred = credentials.Certificate(
    r"C:\ruta\segura\serviceAccountKey.json"
)
firebase_admin.initialize_app(cred)

auth.set_custom_user_claims(
    "PEGA_AQUI_EL_UID",
    {"admin": True}
)
print("Permiso de administrador asignado")