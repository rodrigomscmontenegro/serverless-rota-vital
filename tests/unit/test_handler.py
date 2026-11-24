
import json
from unittest.mock import patch

import pytest

from hello_world import app


@pytest.fixture(autouse=True)
def reset_counter(monkeypatch):
    monkeypatch.setattr(app, "contador", 0)


def create_event(pedido):
    return {"body": json.dumps(pedido)}


def test_generate_transport_guide():
    event = create_event({
        "requisicaoId": "R-001",
        "hospital": "H-Recife",
        "bolsas": ["O-NEG-0142"],
    })

    response = app.lambda_handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert data["guia"] == "G-R-001"
    assert data["hospital"] == "H-Recife"
    assert data["bolsas"] == ["O-NEG-0142"]
    assert data["invocacaoNesteAmbiente"] == 1


def test_missing_request_id():
    event = create_event({
        "hospital": "H-Recife",
    })

    response = app.lambda_handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 400
    assert data["erro"] == "requisicaoId obrigatório"


def test_default_empty_bags():
    event = create_event({
        "requisicaoId": "R-002",
        "hospital": "H-Caruaru",
    })

    response = app.lambda_handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert data["bolsas"] == []


def test_missing_hospital():
    event = create_event({
        "requisicaoId": "R-003",
    })

    response = app.lambda_handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert data["hospital"] is None


def test_invocation_counter():
    event = create_event({
        "requisicaoId": "R-004",
    })

    first = app.lambda_handler(event, None)
    second = app.lambda_handler(event, None)
    third = app.lambda_handler(event, None)

    assert json.loads(first["body"])["invocacaoNesteAmbiente"] == 1
    assert json.loads(second["body"])["invocacaoNesteAmbiente"] == 2
    assert json.loads(third["body"])["invocacaoNesteAmbiente"] == 3


def test_delayed_request():
    event = create_event({
        "requisicaoId": "R-005",
        "demorar": True,
    })

    with patch("hello_world.app.time.sleep") as mock_sleep:
        response = app.lambda_handler(event, None)

        mock_sleep.assert_called_once_with(5)

    assert response["statusCode"] == 201
