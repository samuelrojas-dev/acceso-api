from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# =========================
# CREAR BASE DE DATOS
# =========================

def crear_tabla():
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            telefono TEXT PRIMARY KEY,
            activo BOOLEAN,
            baneado BOOLEAN,
            premium BOOLEAN,
            vencido BOOLEAN
        )
    """)

    conn.commit()
    conn.close()

crear_tabla()

# =========================
# MODELO CREAR CLIENTE
# =========================

class ClienteCreate(BaseModel):
    telefono: str
    activo: bool
    baneado: bool
    premium: bool
    vencido: bool

# =========================
# CREAR CLIENTE
# =========================

@app.post("/crear_cliente")
def crear_cliente(cliente: ClienteCreate):
    try:
        conn = sqlite3.connect("clientes.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO clientes (telefono, activo, baneado, premium, vencido)
            VALUES (?, ?, ?, ?, ?)
        """, (
            cliente.telefono,
            cliente.activo,
            cliente.baneado,
            cliente.premium,
            cliente.vencido
        ))

        conn.commit()
        conn.close()

        return {
            "creado": True,
            "telefono": cliente.telefono
        }

    except sqlite3.IntegrityError:
        return {
            "creado": False,
            "error": "El cliente ya existe"
        }

# =========================
# ACTUALIZAR CLIENTE
# =========================

@app.put("/actualizar_cliente")
def actualizar_cliente(
    telefono: str,
    activo: bool = None,
    baneado: bool = None,
    premium: bool = None,
    vencido: bool = None
):
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clientes WHERE telefono = ?", (telefono,))
    cliente = cursor.fetchone()

    if not cliente:
        conn.close()
        return {
            "actualizado": False,
            "error": "Cliente no existe"
        }

    if activo is not None:
        cursor.execute("UPDATE clientes SET activo = ? WHERE telefono = ?", (activo, telefono))

    if baneado is not None:
        cursor.execute("UPDATE clientes SET baneado = ? WHERE telefono = ?", (baneado, telefono))

    if premium is not None:
        cursor.execute("UPDATE clientes SET premium = ? WHERE telefono = ?", (premium, telefono))

    if vencido is not None:
        cursor.execute("UPDATE clientes SET vencido = ? WHERE telefono = ?", (vencido, telefono))

    conn.commit()
    conn.close()

    return {
        "actualizado": True,
        "telefono": telefono
    }

# =========================
# LISTAR CLIENTES
# =========================

@app.get("/listar_clientes")
def listar_clientes():
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    conn.close()

    resultado = []

    for cliente in clientes:
        resultado.append({
            "telefono": cliente[0],
            "activo": cliente[1],
            "baneado": cliente[2],
            "premium": cliente[3],
            "vencido": cliente[4]
        })

    return resultado

# =========================
# MOTOR DE VALIDACIÓN
# =========================

def validar_acceso(telefono):
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clientes WHERE telefono = ?", (telefono,))
    cliente = cursor.fetchone()

    conn.close()

    if not cliente:
        return {
            "aprobado": False,
            "motivo": "Cliente no existe"
        }

    telefono, activo, baneado, premium, vencido = cliente

    if baneado:
        return {
            "aprobado": False,
            "motivo": "Usuario baneado"
        }

    if not activo:
        return {
            "aprobado": False,
            "motivo": "Usuario inactivo"
        }

    if vencido:
        return {
            "aprobado": False,
            "motivo": "Suscripción vencida"
        }

    return {
        "aprobado": True,
        "motivo": "Acceso concedido"
    }

# =========================
# ENDPOINT VALIDAR
# =========================

@app.get("/validar")
def validar(telefono: str):
    return validar_acceso(telefono)