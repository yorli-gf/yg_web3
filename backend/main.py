# Backend fusionado — versión completa
import datetime
import logging
import os, sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from prometheus_fastapi_instrumentator import Instrumentator
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

# -------------------- LOGGER SETUP --------------------
logger = logging.getLogger("custom_logger")
logging_data = os.getenv("LOG_LEVEL", "INFO").upper()

if logging_data == "DEBUG":
    logger.setLevel(logging.DEBUG)
elif logging_data == "INFO":
    logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logger.level)
formatter = logging.Formatter("%(levelname)s: %(asctime)s - %(name)s - %(message)s")
console_handler.setFormatter(formatter)

loki_handler = LokiLoggerHandler(
    url="http://loki:3100/loki/api/v1/push",
    labels={"application": "FastApi"},
    label_keys={},
    timeout=10,
)

logger.addHandler(loki_handler)
logger.addHandler(console_handler)
logger.info("Logger initialized")

# -------------------- FASTAPI APP --------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- MONGO --------------------
mongo_client = MongoClient("mongodb://admin_user:web3@mongo:27017/")
database = mongo_client.practica1
collection_historial = database.historial

# -------------------- MODELOS --------------------
class Operacion(BaseModel):
    numeros: List[float]

class OperacionLote(BaseModel):
    operacion: str
    numeros: List[float]

class LoteOperaciones(BaseModel):
    operaciones: List[OperacionLote]

# -------------------- VALIDACIONES --------------------
def validar_numeros(numeros: List[float], operacion: str):
    for n in numeros:
        if n < 0:
            logger.error(f"Operación {operacion} fallida — número negativo: {numeros}")
            raise HTTPException(status_code=400, detail={"error": "No se permiten números negativos", "operacion": operacion, "numeros": numeros})

def guardar_historial(operacion: str, numeros: List[float], resultado: float):
    document = {
        "operacion": operacion,
        "numeros": numeros,
        "resultado": resultado,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    collection_historial.insert_one(document)

# -------------------- ENDPOINTS --------------------
@app.post("/calculadora/sum")
def sumar(data: Operacion):
    try:
        validar_numeros(data.numeros, "suma")
        result = sum(data.numeros)
        guardar_historial("suma", data.numeros, result)
        logger.info(f"Operación suma exitosa — {data.numeros} = {result}")
        return {"operacion": "suma", "numeros": data.numeros, "resultado": result}
    except Exception as e:
        logger.error(f"Error en suma: {e}")
        raise

@app.post("/calculadora/sub")
def restar(data: Operacion):
    try:
        validar_numeros(data.numeros, "resta")
        result = data.numeros[0]
        for n in data.numeros[1:]: result -= n
        guardar_historial("resta", data.numeros, result)
        logger.info(f"Operación resta exitosa — {data.numeros} = {result}")
        return {"operacion": "resta", "numeros": data.numeros, "resultado": result}
    except Exception as e:
        logger.error(f"Error en resta: {e}")
        raise

@app.post("/calculadora/mul")
def multiplicar(data: Operacion):
    try:
        validar_numeros(data.numeros, "multiplicación")
        result = 1
        for n in data.numeros: result *= n
        guardar_historial("multiplicación", data.numeros, result)
        logger.info(f"Operación multiplicación exitosa — {data.numeros} = {result}")
        return {"operacion": "multiplicación", "numeros": data.numeros, "resultado": result}
    except Exception as e:
        logger.error(f"Error en multiplicación: {e}")
        raise

@app.post("/calculadora/div")
def dividir(data: Operacion):
    try:
        validar_numeros(data.numeros, "división")
        if 0 in data.numeros[1:]:
            logger.error(f"Intento de división entre cero — {data.numeros}")
            raise HTTPException(status_code=403, detail={"error": "No se puede dividir entre cero", "numeros": data.numeros})
        result = data.numeros[0]
        for n in data.numeros[1:]: result /= n
        guardar_historial("división", data.numeros, result)
        logger.info(f"Operación división exitosa — {data.numeros} = {result}")
        return {"operacion": "división", "numeros": data.numeros, "resultado": result}
    except Exception as e:
        logger.error(f"Error en división: {e}")
        raise

@app.get("/calculadora/historial")
def obtener_historial(
    operacion: Optional[str] = Query(None),
    fecha: Optional[str] = Query(None),
    ordenar_por: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc"),
):
    try:
        filtro = {}
        if operacion: filtro["operacion"] = operacion
        if fecha:
            fecha_inicio = datetime.datetime.fromisoformat(fecha)
            fecha_fin = fecha_inicio + datetime.timedelta(days=1)
            filtro["date"] = {"$gte": fecha_inicio, "$lt": fecha_fin}
        sort = None
        if ordenar_por: sort = [(ordenar_por, 1 if orden == "asc" else -1)]
        operaciones = collection_historial.find(filtro, {'_id': 0}, sort=sort)
        historial = [
            {
                "operacion": op.get("operacion", "desconocida"),
                "numeros": op.get("numeros", []),
                "resultado": op.get("resultado", 0),
                "date": op.get("date").isoformat(),
            }
            for op in operaciones
        ]
        logger.info("Operación historial exitosa")
        return {"historial": historial}
    except Exception as e:
        logger.error(f"Error al obtener historial: {e}")
        raise

@app.post("/calculadora/lote")
def ejecutar_lote(data: LoteOperaciones):
    try:
        resultados = []
        for op in data.operaciones:
            validar_numeros(op.numeros, op.operacion)
            if op.operacion == "división" and 0 in op.numeros[1:]:
                logger.error(f"Intento de división entre cero en lote — {op.numeros}")
                raise HTTPException(status_code=403, detail="No se puede dividir entre cero")
        for op in data.operaciones:
            if op.operacion == "suma": result = sum(op.numeros)
            elif op.operacion == "resta":
                result = op.numeros[0]
                for n in op.numeros[1:]: result -= n
            elif op.operacion == "multiplicación":
                result = 1
                for n in op.numeros: result *= n
            elif op.operacion == "división":
                result = op.numeros[0]
                for n in op.numeros[1:]: result /= n
            guardar_historial(op.operacion, op.numeros, result)
            resultados.append({"operacion": op.operacion, "numeros": op.numeros, "resultado": result})
        logger.info("Operación lote exitosa")
        return {"resultados": resultados}
    except Exception as e:
        logger.error(f"Error en lote: {e}")
        raise

Instrumentator().instrument(app).expose(app)
