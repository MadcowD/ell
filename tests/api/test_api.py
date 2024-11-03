from datetime import timezone
from logging import DEBUG
from uuid import uuid4
import pytest
from typing import Any, Dict
from fastapi.testclient import TestClient

from ell.api.client import EllSqliteClient
from ell.api.server import create_app, get_pubsub, get_serializer
from ell.api.config import Config
from ell.api.logger import setup_logging
from ell.types.serialize import utc_now
from ell.stores.studio import SerializedLMP
from ell.types.lmp import LMPType
from ell.types.serialize import WriteLMPInput


@pytest.fixture
def sql_store() -> EllSqliteClient:
    return EllSqliteClient(":memory:")


def test_construct_serialized_lmp():
    serialized_lmp = SerializedLMP(
        lmp_id="test_lmp_id",
        name="Test LMP",
        source="def test_function(): pass",
        dependencies=str(["dep1", "dep2"]),
        lmp_type=LMPType.LM,
        api_params={"param1": "value1"},
        version_number=1,
        # uses={"used_lmp_1": {}, "used_lmp_2": {}},
        initial_global_vars={"global_var1": "value1"},
        initial_free_vars={"free_var1": "value2"},
        commit_message="Initial commit",
        created_at=utc_now()
    )
    assert serialized_lmp.lmp_id == "test_lmp_id"
    assert serialized_lmp.name == "Test LMP"
    assert serialized_lmp.source == "def test_function(): pass"
    assert serialized_lmp.dependencies == str(["dep1", "dep2"])
    assert serialized_lmp.api_params == {"param1": "value1"}
    assert serialized_lmp.version_number == 1
    assert serialized_lmp.created_at is not None


def test_write_lmp_input():
    # Should be able to construct a WriteLMPInput from data
    input = WriteLMPInput(
        lmp_id="test_lmp_id",
        name="Test LMP",
        source="def test_function(): pass",
        dependencies=str(["dep1", "dep2"]),
        lmp_type=LMPType.LM,
        api_params={"param1": "value1"},
        initial_global_vars={"global_var1": "value1"},
        initial_free_vars={"free_var1": "value2"},
        commit_message="Initial commit",
        version_number=1,
    )

    # Should default a created_at to utc_now
    assert input.created_at is not None
    assert input.created_at.tzinfo == timezone.utc

    # Should be able to construct a SerializedLMP from a WriteLMPInput
    model = SerializedLMP(**input.model_dump())
    assert model.created_at == input.created_at

    input2 = WriteLMPInput(
        lmp_id="test_lmp_id",
        name="Test LMP",
        source="def test_function(): pass",
        dependencies=str(["dep1", "dep2"]),
        lmp_type=LMPType.LM,
        api_params={"param1": "value1"},
        initial_global_vars={"global_var1": "value1"},
        initial_free_vars={"free_var1": "value2"},
        commit_message="Initial commit",
        version_number=1,
        # should work with an isoformat string
        created_at=utc_now().isoformat()  # type: ignore
    )
    model2 = SerializedLMP(**input2.model_dump())
    assert model2.created_at == input2.created_at
    assert input2.created_at is not None
    assert input2.created_at.tzinfo == timezone.utc


def create_test_app(sql_store: EllSqliteClient):
    setup_logging(DEBUG)
    config = Config(storage_dir=":memory:")
    app = create_app(config)

    publisher = None

    async def get_publisher_override():
        yield publisher


    def get_serializer_override():
        return sql_store

    app.dependency_overrides[get_pubsub] = get_publisher_override
    app.dependency_overrides[get_serializer] = get_serializer_override

    client = TestClient(app)

    return app, client, publisher, config


def test_write_lmp(sql_store: EllSqliteClient):
    _app, client, *_ = create_test_app(sql_store)

    # fime. figure out what's going on with `uses`
    lmp_data: Dict[str, Any] = {
        "lmp_id": uuid4().hex,
        "name": "Test LMP",
        "source": "def test_function(): pass",
        "dependencies": str(["dep1", "dep2"]),
        "lmp_type": LMPType.LM,
        "api_params": {"param1": "value1"},
        "version_number": 1,
        # "uses": {"used_lmp_1": {}, "used_lmp_2": {}},
        "initial_global_vars": {"global_var1": "value1"},
        "initial_free_vars": {"free_var1": "value2"},
        "commit_message": "Initial commit",
        "created_at": utc_now().isoformat().replace("+00:00", "Z")
    }
    # uses: List[str] = {"used_lmp_1": {}, "used_lmp_2": {}},

    response = client.post(
        "/lmp",
        json={
            "lmp": lmp_data,
            "uses": []
        }
    )

    assert response.status_code == 200

    lmp = client.get(f"/lmp/{lmp_data['lmp_id']}")
    assert lmp.status_code == 200
    # del lmp_data["uses"]
    assert lmp.json() == {**lmp_data, "num_invocations": 0}


def test_write_invocation(sql_store: EllSqliteClient):
    _app, client, *_ = create_test_app(sql_store)

    lmp_id = uuid4().hex
    lmp_data: Dict[str, Any] = {
        "lmp_id": lmp_id,
        "name": "Test LMP",
        "source": "def test_function(): pass",
        "dependencies": str(["dep1", "dep2"]),
        "lmp_type": LMPType.LM,
        "api_params": {"param1": "value1"},
    }
    response = client.post(
        "/lmp",
        json={'lmp': lmp_data, 'uses': []}
    )
    try:
        assert response.status_code == 200
    except Exception as e:
        print(response.json())
        raise e

    invocation_data = {
        "id": uuid4().hex,
        "lmp_id": lmp_id,
        "args": ["arg1", "arg2"],
        "kwargs": {"kwarg1": "value1"},
        "global_vars": {"global_var1": "value1"},
        "free_vars": {"free_var1": "value2"},
        "latency_ms": 100.0,
        "invocation_kwargs": {"model": "gpt-4o", "messages": [{"role": "system", "content": "You are a JSON parser. You respond only in JSON. Do not format using markdown."}, {"role": "user", "content": "You are given the following task: \"What is two plus two?\"\n            Parse the task into the following type:\n            {'$defs': {'Add': {'properties': {'op': {'const': '+', 'enum': ['+'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Add', 'type': 'object'}, 'Div': {'properties': {'op': {'const': '/', 'enum': ['/'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Div', 'type': 'object'}, 'Mul': {'properties': {'op': {'const': '*', 'enum': ['*'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Mul', 'type': 'object'}, 'Sub': {'properties': {'op': {'const': '-', 'enum': ['-'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Sub', 'type': 'object'}}, 'anyOf': [{'$ref': '#/$defs/Add'}, {'$ref': '#/$defs/Sub'}, {'$ref': '#/$defs/Mul'}, {'$ref': '#/$defs/Div'}]}\n            "}], "lm_kwargs": {"temperature": 0.1}, "client": None},
        "contents": { }
    }
    consumes_data = []

    input = {
        "invocation": invocation_data,
        "consumes": consumes_data
    }
    response = client.post(
        "/invocation",
        json=input
    )

    print(response.json())
    assert response.status_code == 200
    # assert response.json() == input


if __name__ == "__main__":
    pytest.main()
