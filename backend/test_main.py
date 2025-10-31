import pytest
import mongomock
from fastapi.testclient import TestClient
import main
from main import app

# Base de datos y colección falsas
fake_mongo_client = mongomock.MongoClient()
fake_database = fake_mongo_client.practica1
fake_collection_historia = fake_database.historial  # 👈 mismo nombre que en main

client = TestClient(app)


@pytest.mark.parametrize(
    "numeroa, numerob, resultado",
    [
        (5, 10, 15),
        (0, 0, 0),
        (-5, 5, 0),
        (-10, -5, -15),
        (2.5, 2.5, 5.0),
        (10, -20, -10),
    ],
)
def test_sumar(monkeypatch, numeroa, numerob, resultado):
    # 👇 Reemplaza la colección real por la falsa
    monkeypatch.setattr(main, "collection_historia", fake_collection_historia)

    response = client.get(f"/calculadora/sum?a={numeroa}&b={numerob}")
    assert response.status_code == 200
    assert response.json() == {"a": numeroa, "b": numerob, "resultado": resultado}

    # Verifica que realmente se insertó en la colección falsa
    inserted = list(fake_collection_historia.find({"a": numeroa, "b": numerob}))
    assert len(inserted) > 0  # ✅ confirma que guardó algo


def test_historial(monkeypatch):
    monkeypatch.setattr(main, "collection_historia", fake_collection_historia)

    response = client.get("/calculadora/historial")
    assert response.status_code == 200

    expected_data = list(fake_collection_historia.find({}))
    historial = [
        {
            "a": doc["a"],
            "b": doc["b"],
            "resultado": doc["resultado"],
            "date": doc["date"].isoformat(),
        }
        for doc in expected_data
    ]

    assert response.json() == {"historia": historial}
