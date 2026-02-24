from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

app = FastAPI()

# Base de datos en memoria (temporal)
clientes = {}

# -----------------------------------
# HOME
# -----------------------------------

@app.get("/")
def home():
    return {"mensaje": "API AccessCheck funcionando correctamente"}

# -----------------------------------
# CREAR CLIENTE
# -----------------------------------

@app.post("/crear")
async def crear_cliente(data: dict):
    nombre = data.get("nombre")

    if nombre in clientes:
        return JSONResponse(
            status_code=200,
            content={"creado": False, "error": "El cliente ya existe"}
        )

    clientes[nombre] = {
        "saldo": data.get("saldo", 0),
        "premium": data.get("premium", False),
        "deudas": data.get("deudas", False),
        "baneado": data.get("baneado", False)
    }

    return {"creado": True, "cliente": clientes[nombre]}

# -----------------------------------
# VALIDAR RETIRO
# -----------------------------------

@app.post("/validar")
async def validar_retiro(data: dict):
    nombre = data.get("nombre")

    if nombre not in clientes:
        return {"aprobado": False, "motivo": "Cliente no existe"}

    cliente = clientes[nombre]

    # PRIORIDAD 1: baneado
    if cliente["baneado"]:
        return {"aprobado": False, "motivo": "Cliente baneado"}

    # PRIORIDAD 2: saldo suficiente
    if cliente["saldo"] <= 50:
        return {"aprobado": False, "motivo": "Saldo insuficiente"}

    # PRIORIDAD 3: deudas
    if cliente["deudas"] and not cliente["premium"]:
        return {"aprobado": False, "motivo": "Tiene deudas y no es premium"}

    return {"aprobado": True, "motivo": "Puede retirar dinero"}

# -----------------------------------
# WEBHOOK WHATSAPP (Twilio)
# -----------------------------------

@app.post("/webhook")
async def recibir_mensaje(request: Request):
    form = await request.form()
    mensaje = form.get("Body")
    numero = form.get("From")

    print(f"Mensaje recibido de {numero}: {mensaje}")

    return PlainTextResponse("OK")