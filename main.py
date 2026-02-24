from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from twilio.twiml.messaging_response import MessagingResponse
import sqlite3
import requests

app = FastAPI()

# =====================================================
# BASE DE DATOS SQLITE
# =====================================================

def crear_bd():
    conn = sqlite3.connect("accesscheck.db")
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
        nombre TEXT PRIMARY KEY,
        saldo REAL DEFAULT 0,
        premium INTEGER DEFAULT 0,
        deudas INTEGER DEFAULT 0,
        baneado INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()

crear_bd()

# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():
    return {"mensaje": "API AccessCheck funcionando correctamente"}

# =====================================================
# CREAR CLIENTE
# =====================================================

@app.post("/crear")
async def crear_cliente(data: dict):
    nombre = data.get("nombre")

    if not nombre:
        return {"creado": False, "error": "Debe enviar nombre"}

    conn = sqlite3.connect("accesscheck.db")
    cursor = conn.cursor()

    cursor.execute("SELECT nombre FROM clientes WHERE nombre=?", (nombre,))
    if cursor.fetchone():
        conn.close()
        return JSONResponse(
            status_code=200,
            content={"creado": False, "error": "El cliente ya existe"}
        )

    cursor.execute('''
        INSERT INTO clientes (nombre, saldo, premium, deudas, baneado)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        nombre,
        data.get("saldo", 0),
        int(data.get("premium", False)),
        int(data.get("deudas", False)),
        int(data.get("baneado", False))
    ))

    conn.commit()
    conn.close()

    return {"creado": True, "cliente": data}

# =====================================================
# VALIDAR RETIRO
# =====================================================

@app.post("/validar")
async def validar_retiro(data: dict):
    nombre = data.get("nombre")

    conn = sqlite3.connect("accesscheck.db")
    cursor = conn.cursor()
    cursor.execute("SELECT saldo, premium, deudas, baneado FROM clientes WHERE nombre=?", (nombre,))
    fila = cursor.fetchone()
    conn.close()

    if not fila:
        return {"aprobado": False, "motivo": "Cliente no existe"}

    saldo, premium, deudas, baneado = fila
    premium = bool(premium)
    deudas = bool(deudas)
    baneado = bool(baneado)

    if baneado:
        return {"aprobado": False, "motivo": "Cliente baneado"}
    if saldo <= 50:
        return {"aprobado": False, "motivo": "Saldo insuficiente"}
    if deudas and not premium:
        return {"aprobado": False, "motivo": "Tiene deudas y no es premium"}

    return {"aprobado": True, "motivo": "Puede retirar dinero"}

# =====================================================
# WEBHOOK WHATSAPP (TWILIO)
# =====================================================

@app.post("/webhook")
async def recibir_mensaje(request: Request):
    form = await request.form()
    mensaje = form.get("Body")
    numero = form.get("From")

    print(f"Mensaje recibido de {numero}: {mensaje}")

    resp = MessagingResponse()

    if mensaje.lower().startswith("validar"):
        partes = mensaje.split()

        if len(partes) < 2:
            resp.message("Debes escribir: validar TU_NOMBRE")
        else:
            nombre = partes[1]

            # Llamamos a nuestra propia API
            url = "https://acceso-api-2lxd.onrender.com/validar"
            data = {"nombre": nombre}

            try:
                r = requests.post(url, json=data, timeout=5)
                resultado = r.json()
                texto = f"Aprobado: {resultado['aprobado']}\nMotivo: {resultado['motivo']}"
            except Exception as e:
                texto = f"Error al validar: {e}"

            resp.message(texto)
    else:
        resp.message("Escribe: validar TU_NOMBRE")

    return PlainTextResponse(str(resp), media_type="application/xml")