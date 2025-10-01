# tests/test_api.py
import datetime
import pytest
from fastapi.testclient import TestClient
from backend import main  

# Mock mínimo de Mongo
class MockCollection:
    def __init__(self):
        self._docs = []

    def insert_one(self, doc):
        # guardamos copia para evitar referencias
        copy = dict(doc)
        self._docs.append(copy)
        class InsertResult:
            inserted_id = None
        return InsertResult()

    def find(self, filtro=None, projection=None, sort=None):
        docs = list(self._docs)

        filtro = filtro or {}
        # filtrar por operacion
        if "operacion" in filtro:
            docs = [d for d in docs if d.get("operacion") == filtro["operacion"]]

        # filtrar por fecha con rango
        if "date" in filtro:
            rng = filtro["date"]
            g = rng.get("$gte")
            l = rng.get("$lt")
            docs = [d for d in docs if "date" in d and g <= d["date"] < l]

        if sort:
            key, order = sort[0]
            reverse = order == -1
            docs.sort(key=lambda d: d.get(key, 0), reverse=reverse)

        for d in docs:
            yield d

# Fixture que parchea la colección
@pytest.fixture
def client_and_mock(monkeypatch):
    """Reemplaza main.collection_historial por MockCollection y devuelve TestClient"""
    mc = MockCollection()
    monkeypatch.setattr(main, "collection_historial", mc)
    client = TestClient(main.app)
    return client, mc

# Tests operaciones correctas
@pytest.mark.parametrize("endpoint, payload, expected", [
    ("/calculadora/sum", {"numeros":[1,2,3]}, 6),
    ("/calculadora/sub", {"numeros":[10,3]}, 7),
    ("/calculadora/mul", {"numeros":[2,3,4]}, 24),
    ("/calculadora/div", {"numeros":[100,5,2]}, 10),
])
def test_operaciones_exitosas(client_and_mock, endpoint, payload, expected):
    client, mc = client_and_mock
    r = client.post(endpoint, json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["resultado"] == expected
    assert len(mc._docs) == 1
    assert mc._docs[0]["resultado"] == expected
    mc._docs.clear()

# Tests errores: negativos 
@pytest.mark.parametrize("endpoint", [
    "/calculadora/sum",
    "/calculadora/sub",
    "/calculadora/mul",
    "/calculadora/div",
])
def test_numeros_negativos_rechazados(client_and_mock, endpoint):
    client, mc = client_and_mock
    r = client.post(endpoint, json={"numeros":[-1, 5]})
    assert r.status_code == 400
    body = r.json()
    assert "detail" in body
    detail = body["detail"]
    assert isinstance(detail, dict)
    assert detail.get("error") == "No se permiten números negativos"
    assert len(mc._docs) == 0

# Test división entre cero 
def test_division_por_cero_rechazada(client_and_mock):
    client, mc = client_and_mock
    r = client.post("/calculadora/div", json={"numeros":[10, 0]})
    assert r.status_code == 403
    body = r.json()
    assert "detail" in body
    detail = body["detail"]
    assert isinstance(detail, dict)
    assert detail.get("error") == "No se puede dividir entre cero"
    assert len(mc._docs) == 0

# Test endpoint lote 

def test_lote_exitoso(client_and_mock):
    client, mc = client_and_mock
    payload = {
        "operaciones": [
            {"operacion":"suma", "numeros":[1,2]},
            {"operacion":"resta", "numeros":[10,3]},
            {"operacion":"multiplicación", "numeros":[2,3]}
        ]
    }
    r = client.post("/calculadora/lote", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "resultados" in body
    assert len(body["resultados"]) == 3
    # historial recibió 3 inserciones
    assert len(mc._docs) == 3


# Test lote negativo 

def test_lote_error_indica_operacion_y_numeros(client_and_mock):
    client, mc = client_and_mock
    payload = {
        "operaciones": [
            {"operacion":"suma", "numeros":[1,2]},
            {"operacion":"resta", "numeros":[-5,1]},  
            {"operacion":"multiplicación", "numeros":[2,3]}
        ]
    }
    r = client.post("/calculadora/lote", json=payload)
    assert r.status_code == 400
    body = r.json()
    assert "detail" in body
    detail = body["detail"]
    # detalle debe decir que operación y números causaron el fallo
    assert detail.get("operacion") in ["resta", "suma", "multiplicación"]
    assert "numeros" in detail
    # No debe haberse insertado nada por el fallo
    assert len(mc._docs) == 0

# Test historial: filtros y ordenamiento
def test_historial_filtros_y_orden(client_and_mock):
    client, mc = client_and_mock
    # agregamos 3 documentos con fechas y resultados distintos
    dt1 = datetime.datetime(2025, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
    dt2 = datetime.datetime(2025, 1, 2, 10, 0, tzinfo=datetime.timezone.utc)
    dt3 = datetime.datetime(2025, 1, 3, 10, 0, tzinfo=datetime.timezone.utc)

    mc.insert_one({"operacion":"suma", "numeros":[1,2], "resultado":3, "date": dt1})
    mc.insert_one({"operacion":"resta", "numeros":[10,1], "resultado":9, "date": dt2})
    mc.insert_one({"operacion":"suma", "numeros":[5,5], "resultado":10, "date": dt3})

    # filtrar por operacion suma -> debe devolverse 2 items
    r = client.get("/calculadora/historial", params={"operacion":"suma"})
    assert r.status_code == 200
    lista = r.json()["historial"]
    assert len(lista) == 2

    # ordenar por resultado descendente
    r2 = client.get("/calculadora/historial", params={"ordenar_por":"resultado", "orden":"desc"})
    assert r2.status_code == 200
    lista2 = r2.json()["historial"]
    # primero debe ser el resultado mayor (10)
    assert lista2[0]["resultado"] == 10
