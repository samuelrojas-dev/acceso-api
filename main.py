from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from twilio.twiml.messaging_response import MessagingResponse

app = FastAPI()

# =====================================================
# BASE DE DATOS TEMPORAL EN MEMORIA
# =====================================================

clientes = {}

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

# =====================================================
# VALIDAR RETIRO
# =====================================================

@app.post("/validar")
async def validar_retiro(data: dict):
    nombre = data.get("nombre")

    if nombre not in clientes:
        return {"aprobado": False, "motivo": "Cliente no existe"}

    cliente = clientes[nombre]

    # PRIORIDAD 1 → baneado
    if cliente["baneado"]:
        return {"aprobado": False, "motivo": "Cliente baneado"}

    # PRIORIDAD 2 → saldo suficiente (>50)
    if cliente["saldo"] <= 50:
        return {"aprobado": False, "motivo": "Saldo insuficiente"}

    # PRIORIDAD 3 → deudas
    if cliente["deudas"] and not cliente["premium"]:
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

    respuesta = MessagingResponse()

    # Si el usuario escribe "validar Samuel"
    if mensaje and mensaje.lower().startswith("validar"):
        partes = mensaje.split()

        if len(partes) < 2:
            respuesta.message("Debes escribir: validar NOMBRE")
        else:
            nombre = partes[1]

            if nombre not in clientes:
                respuesta.message("Cliente no existe")
            else:
                cliente = clientes[nombre]

                if cliente["baneado"]:
                    respuesta.message("❌ Cliente baneado")
                elif cliente["saldo"] <= 50:
                    respuesta.message("❌ Saldo insuficiente")
                elif cliente["deudas"] and not cliente["premium"]:
                    respuesta.message("❌ Tiene deudas y no es premium")
                else:
                    respuesta.message("✅ Puede retirar dinero")

    else:
        respuesta.message("Escribe: validar TU_NOMBRE")

    return Response(content=str(respuesta), media_type="application/xml")