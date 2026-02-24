from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
import psycopg
import os

app = FastAPI()

# =====================================================
# CONEXIÓN A SUPABASE (PostgreSQL - psycopg v3)
# =====================================================

def get_conn():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=5432
    )

# =====================================================
# CREAR TABLA SI NO EXISTE
# =====================================================

def crear_tabla():
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    nombre TEXT PRIMARY KEY,
                    membresia_activa BOOLEAN DEFAULT FALSE,
                    bloqueado BOOLEAN DEFAULT FALSE,
                    nivel TEXT DEFAULT 'basico'
                )
            """)
        conn.commit()

crear_tabla()

# =====================================================
# LÓGICA DE VALIDACIÓN DE ACCESO
# =====================================================

def validar_acceso(nombre: str):
    with get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT membresia_activa, bloqueado, nivel FROM clientes WHERE nombre=%s",
                (nombre,)
            )
            fila = cursor.fetchone()

    if not fila:
        return {"aprobado": False, "motivo": "Usuario no registrado"}

    membresia_activa, bloqueado, nivel = fila

    if bloqueado:
        return {"aprobado": False, "motivo": "Usuario bloqueado"}

    if not membresia_activa:
        return {"aprobado": False, "motivo": "Membresía inactiva"}

    return {"aprobado": True, "motivo": f"Acceso {nivel} activo"}

# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():
    return {"mensaje": "Sistema de acceso funcionando correctamente"}

# =====================================================
# CREAR USUARIO
# =====================================================

@app.post("/crear")
async def crear_usuario(data: dict):
    nombre = data.get("nombre")

    if not nombre:
        return {"creado": False, "error": "Debe enviar nombre"}

    with get_conn() as conn:
        with conn.cursor() as cursor:

            cursor.execute("SELECT nombre FROM clientes WHERE nombre=%s", (nombre,))
            if cursor.fetchone():
                return {"creado": False, "error": "El usuario ya existe"}

            cursor.execute("""
                INSERT INTO clientes (nombre, membresia_activa, bloqueado, nivel)
                VALUES (%s, %s, %s, %s)
            """, (
                nombre,
                data.get("membresia_activa", False),
                data.get("bloqueado", False),
                data.get("nivel", "basico")
            ))

        conn.commit()

    return {"creado": True, "usuario": data}

# =====================================================
# VALIDAR ACCESO (API)
# =====================================================

@app.post("/validar")
async def validar(data: dict):
    nombre = data.get("nombre")
    return validar_acceso(nombre)

# =====================================================
# WEBHOOK WHATSAPP (TWILIO)
# =====================================================

@app.post("/webhook")
async def recibir_mensaje(request: Request):
    form = await request.form()
    mensaje = form.get("Body")

    resp = MessagingResponse()

    if mensaje and mensaje.lower().startswith("validar"):
        partes = mensaje.split()

        if len(partes) < 2:
            resp.message("Escribe: validar TU_NOMBRE")
        else:
            nombre = partes[1]
            resultado = validar_acceso(nombre)

            if resultado["aprobado"]:
                texto = f"✅ {resultado['motivo']}. Puedes ingresar."
            else:
                texto = f"❌ {resultado['motivo']}."

            resp.message(texto)
    else:
        resp.message("Bienvenido 👋\nEscribe: validar TU_NOMBRE")

    return PlainTextResponse(str(resp), media_type="application/xml")