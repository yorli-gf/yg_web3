import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo_client = MongoClient("mongodb://admin_user:web3@mongo:27017/")
database = mongo_client.practica1
collection_historial = database.historial


class Operacion(BaseModel):
    numeros: List[float]  

class OperacionLote(BaseModel):
    operacion: str
    numeros: List[float]

class LoteOperaciones(BaseModel):
    operaciones: List[OperacionLote]


def validar_numeros(numeros: List[float], operacion: str):
    """Valida que no haya números negativos"""
    for n in numeros:
        if n < 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No se permiten números negativos",
                    "operacion": operacion,
                    "numeros": numeros,
                },
            )

def guardar_historial(operacion: str, numeros: List[float], resultado: float):
    """Guarda una operación en la colección de Mongo"""
    document = {
        "operacion": operacion,
        "numeros": numeros,
        "resultado": resultado,
        "date": datetime.datetime.now(tz=datetime.timezone.utc),
    }
    collection_historial.insert_one(document)


@app.post("/calculadora/sum")
def sumar(data: Operacion):
    validar_numeros(data.numeros, "suma")
    result = sum(data.numeros)
    guardar_historial("suma", data.numeros, result)
    return {"operacion": "suma", "numeros": data.numeros, "resultado": result}

@app.post("/calculadora/sub")
def restar(data: Operacion):
    validar_numeros(data.numeros, "resta")
    result = data.numeros[0]
    for n in data.numeros[1:]:
        result -= n
    guardar_historial("resta", data.numeros, result)
    return {"operacion": "resta", "numeros": data.numeros, "resultado": result}

@app.post("/calculadora/mul")
def multiplicar(data: Operacion):
    validar_numeros(data.numeros, "multiplicación")
    result = 1
    for n in data.numeros:
        result *= n
    guardar_historial("multiplicación", data.numeros, result)
    return {"operacion": "multiplicación", "numeros": data.numeros, "resultado": result}

@app.post("/calculadora/div")
def dividir(data: Operacion):
    validar_numeros(data.numeros, "división")
    if 0 in data.numeros[1:]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "No se puede dividir entre cero",
                "operacion": "división",
                "numeros": data.numeros,
            },
        )
    result = data.numeros[0]
    for n in data.numeros[1:]:
        result /= n
    guardar_historial("división", data.numeros, result)
    return {"operacion": "división", "numeros": data.numeros, "resultado": result}


@app.get("/calculadora/historial")
def obtener_historial(
    operacion: Optional[str] = Query(None, description="Filtrar por operación (suma, resta, multiplicación, división)"),
    fecha: Optional[str] = Query(None, description="Filtrar por fecha (YYYY-MM-DD)"),
    ordenar_por: Optional[str] = Query(None, description="Campo para ordenar (resultado o date)"),
    orden: Optional[str] = Query("asc", description="asc o desc"),
):
    filtro = {}

    # Filtrar por tipo de operación
    if operacion:
        filtro["operacion"] = operacion

    # Filtrar por fecha (día completo)
    if fecha:
        try:
            fecha_inicio = datetime.datetime.fromisoformat(fecha)
            fecha_fin = fecha_inicio + datetime.timedelta(days=1)
            filtro["date"] = {"$gte": fecha_inicio, "$lt": fecha_fin}
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")

    # Ordenamiento
    sort = None
    if ordenar_por:
        if ordenar_por not in ["resultado", "date"]:
            raise HTTPException(status_code=400, detail="Solo se puede ordenar por 'resultado' o 'date'")
        sort = [(ordenar_por, 1 if orden == "asc" else -1)]

    operaciones = collection_historial.find(filtro, {'_id': 0}, sort=sort)
    historial = []
    for op in operaciones:
        historial.append({
            "operacion": op.get("operacion", "desconocida"),
            "numeros": op.get("numeros", []), 
            "resultado": op.get("resultado", 0),
            "date": op.get("date", datetime.datetime.now()).isoformat(),
        })

    return {"historial": historial}


@app.post("/calculadora/lote")
def ejecutar_lote(data: LoteOperaciones):
    resultados = []
    
    for op in data.operaciones:
        # Validación de negativos
        validar_numeros(op.numeros, op.operacion)
        
        # Validación de división por cero
        if op.operacion == "división" and 0 in op.numeros[1:]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "No se puede dividir entre cero",
                    "operacion": op.operacion,
                    "numeros": op.numeros,
                },
            )
        
        if op.operacion not in ["suma", "resta", "multiplicación", "división"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Operación no soportada: {op.operacion}",
                    "operacion": op.operacion,
                    "numeros": op.numeros,
                },
            )

    for op in data.operaciones:
        # Ejecución de operaciones
        if op.operacion == "suma":
            result = sum(op.numeros)
        elif op.operacion == "resta":
            result = op.numeros[0]
            for n in op.numeros[1:]:
                result -= n
        elif op.operacion == "multiplicación":
            result = 1
            for n in op.numeros:
                result *= n
        elif op.operacion == "división":
            result = op.numeros[0]
            for n in op.numeros[1:]:
                result /= n

        # Guardar en historial
        guardar_historial(op.operacion, op.numeros, result)

        # Agregar a respuesta
        resultados.append({
            "operacion": op.operacion,
            "numeros": op.numeros,
            "resultado": result
        })

    return {"resultados": resultados}