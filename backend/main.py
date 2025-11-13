import datetime
import logging
import os, sys
from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

logger = logging.getLogger("custom_logger")
logging_data = os.getenv("LOG_LEVEL", "INFO").upper()

if logging_data == "DEBUG":
    logger.setLevel(logging.DEBUG)
elif logging_data == "INFO":
    logger.setLevel(logging.INFO)

#Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logger.level)
formatter = logging.Formatter(
    "%(levelname)s: %(asctime)s - %(name)s - %(message)s"
) 
console_handler.setFormatter(formatter)

# Create an instance of the custom handler
loki_handler = LokiLoggerHandler(
    url="http://loki:3100/loki/api/v1/push",
    labels={"application": "FastApi"},
    label_keys={},
    timeout=10,
)

logger.addHandler(loki_handler)
logger.addHandler(console_handler)
logger.info("Logger initialized")

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las orÃ­genes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#MongoDB Colection
mongo_client = MongoClient("mongodb://admin_user:web3@practicas-mongo-1:27017/")
database = mongo_client.practica1
collection_historial = database.historial

@app.get("/calculadora/sum")
def sumar(a: float, b: float):
    """
    Suma de dos nÃºmeros que viene como parÃ¡metros e query (?a=...&b=...)
    Ejemplo: /calculadora/sum?a=5&b=10
    Holi, cambios de back, hi so, si
    """

    result = a + b

    document = {
        "resultado": result,
        "a": a,
        "b": b,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }

    logger.info(f"Operación suma exitosa")
    logger.debug(f"Operación suma a: {a}, b: {b}, resultado: {result}")
    logger.error("Operación suma fallida")  # Ejemplo de log de error

    collection_historial.insert_one(document)

    return {"a": a, "b": b, "resultado": result}

@app.get("/calculadora/historial")
def obtener_historial():
    operaciones = collection_historial.find({})
    historial = []
    for operacion in operaciones:
        historial.append({
            "a": operacion["a"],
            "b": operacion["b"],
            "resultado": operacion["resultado"],
            "date": operacion["date"].isoformat()
        })

    logger.info(f"historial exitosa")
    logger.debug(f"Historial de operaciones: {historial}")

    return {"historial": historial}

Instrumentator().instrument(app).expose(app)