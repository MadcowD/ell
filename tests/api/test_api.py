from datetime import timezone
from logging import DEBUG
from uuid import uuid4
import pytest
from typing import Any, Dict, Tuple

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, ValidationError

import ell
from ell import Message
from ell.serialize.http import EllHTTPSerializer
from ell.serialize.sqlite import SQLiteSerializer, AsyncSQLiteSerializer
from ell.api.server import create_app, get_pubsub, get_serializer
from ell.api.config import Config
from ell.api.logger import setup_logging
from ell.types import ToolCall
from ell.types.serialize import WriteInvocationInput, utc_now, Invocation, InvocationContents
from ell.stores.models import SerializedLMP
from ell.types.lmp import LMPType
from ell.types.serialize import WriteLMPInput


@pytest.fixture
def sqlite_serializer() -> SQLiteSerializer:
    return SQLiteSerializer(":memory:")


@pytest.fixture
def async_sqlite_serializer() -> AsyncSQLiteSerializer:
    return AsyncSQLiteSerializer(":memory:")


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


def create_test_app(serializer: AsyncSQLiteSerializer) -> Tuple[FastAPI, EllHTTPSerializer, None, Config]:
    setup_logging(DEBUG)
    config = Config(storage_dir=":memory:")
    app = create_app(config)

    publisher = None

    async def get_publisher_override():
        yield publisher

    def get_serializer_override():
        return serializer

    app.dependency_overrides[get_pubsub] = get_publisher_override
    app.dependency_overrides[get_serializer] = get_serializer_override

    client = EllHTTPSerializer(client=TestClient(app))

    return app, client, publisher, config


def test_write_lmp(async_sqlite_serializer: AsyncSQLiteSerializer):
    _app, client, *_ = create_test_app(async_sqlite_serializer)

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
        "created_at": utc_now().isoformat().replace("+00:00", "Z"),
        "uses": ['used_lmp_1']
    }

    response = client.client.post("/lmp", json=lmp_data)

    # response = client.write_lmp(
    #     WriteLMPInput(**lmp_data),
    # )

    assert response.status_code == 200

    lmp = client.client.get(f"/lmp/{lmp_data['lmp_id']}")
    assert lmp.status_code == 200
    del lmp_data["uses"] # todo. return uses y/n?
    assert lmp.json() == {**lmp_data, "num_invocations": 0}


def test_write_invocation(async_sqlite_serializer: AsyncSQLiteSerializer):
    _app, client, *_ = create_test_app(async_sqlite_serializer)
    # Test basic http client functionality
    client = client.client

    # first write an lmp..
    lmp_id = uuid4().hex
    lmp_data: Dict[str, Any] = {
        "lmp_id": lmp_id,
        "name": "Test LMP",
        "source": "def test_function(): pass",
        "dependencies": str(["dep1", "dep2"]),
        "lmp_type": LMPType.LM,
        "api_params": {"param1": "value1"},
    }

    response = client.post("/lmp", json=lmp_data)

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
        "invocation_kwargs": {"model": "gpt-4o", "messages": [{"role": "system",
                                                               "content": "You are a JSON parser. You respond only in JSON. Do not format using markdown."},
                                                              {"role": "user",
                                                               "content": "You are given the following task: \"What is two plus two?\"\n            Parse the task into the following type:\n            {'$defs': {'Add': {'properties': {'op': {'const': '+', 'enum': ['+'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Add', 'type': 'object'}, 'Div': {'properties': {'op': {'const': '/', 'enum': ['/'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Div', 'type': 'object'}, 'Mul': {'properties': {'op': {'const': '*', 'enum': ['*'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Mul', 'type': 'object'}, 'Sub': {'properties': {'op': {'const': '-', 'enum': ['-'], 'title': 'Op', 'type': 'string'}, 'a': {'title': 'A', 'type': 'number'}, 'b': {'title': 'B', 'type': 'number'}}, 'required': ['op', 'a', 'b'], 'title': 'Sub', 'type': 'object'}}, 'anyOf': [{'$ref': '#/$defs/Add'}, {'$ref': '#/$defs/Sub'}, {'$ref': '#/$defs/Mul'}, {'$ref': '#/$defs/Div'}]}\n            "}],
                              "lm_kwargs": {"temperature": 0.1}, "client": None},
        "contents": {}
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


class MySampleToolInput(BaseModel):
    sample_property: str = Field("A thing")


@ell.tool()
def my_sample_tool(args: MySampleToolInput = Field(
    description="The full name of a city and country, e.g. San Francisco, CA, USA")):
    return '42'


def test_invocation_json_round_trip():
    # pretend it's being tracked
    my_sample_tool.__ell_hash__ = "lmp-123"
    invocation_id = "invocation-" + uuid4().hex
    tool_call = ToolCall(
        tool=my_sample_tool,
        tool_call_id=uuid4().hex,
        params=MySampleToolInput(sample_property="test"),
    )
    invocation_contents = InvocationContents(
        invocation_id=invocation_id,
        results=[Message(role='user', content=[tool_call])]
    )
    invocation = Invocation(
        id=invocation_id,
        lmp_id=uuid4().hex,
        latency_ms=42.0,
        contents=invocation_contents,
        created_at=utc_now()
    )

    # Serialize
    result = invocation.model_dump()

    # Deserialize
    _invocation=None
    try:
        _invocation = Invocation.model_validate(result)
    except ValidationError as e:
        import json
        print("\nJSON errors:")
        print(json.dumps(e.errors(), default=str,indent=2))

    # Should be equal
    # Except that:
    # ToolCall before / after serialization:
    # 1. `tool` is a function vs a string
    # 2. `params` is a BaseModel (in userland) vs a dictionary
    # These are not equivalent

    # What should be equivalent: deserialized forms of serialized forms
    assert _invocation.model_dump() == result

def test_write_invocation_tool_call(async_sqlite_serializer: AsyncSQLiteSerializer):
    _app, client, *_ = create_test_app(async_sqlite_serializer)
    # Test basic http functionality
    client = client.client

    # first write an lmp..
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
        json=lmp_data
    )
    try:
        assert response.status_code == 200
    except Exception as e:
        print(response.json())
        raise e

    # pretend it's being tracked
    my_sample_tool.__ell_hash__ = "lmp-123"
    invocation_id = "invocation-" + uuid4().hex
    tool_call = ToolCall(
        tool=my_sample_tool,
        tool_call_id=uuid4().hex,
        params=MySampleToolInput(sample_property="test"),
    )
    invocation_contents = InvocationContents(
        invocation_id=invocation_id,
        results=[Message(role='user', content=[tool_call])]
    )
    invocation = Invocation(
        id=invocation_id,
        lmp_id=lmp_id,
        latency_ms=42.0,
        contents=invocation_contents,
        created_at=utc_now()
    )

    response = client.post(
        "/invocation",
        json={'invocation':invocation.model_dump(),'consumes':[]}
    )
    print(response.json())
    assert response.status_code == 200

def test_http_client_write_lmp(async_sqlite_serializer: AsyncSQLiteSerializer):
    _app, client, *_ = create_test_app(async_sqlite_serializer)

    lmp_data: Dict[str, Any] = {
        "lmp_id": uuid4().hex,
        "lmp_type": LMPType.LM,
        "name": "Test LMP",
        "source": "def test_function(): pass",
        "dependencies": str(["dep1", "dep2"]),
    }
    result = client.write_lmp(WriteLMPInput(
        lmp_id=lmp_data["lmp_id"],
        lmp_type=lmp_data["lmp_type"],
        name=lmp_data["name"],
        source=lmp_data["source"],
        dependencies=lmp_data["dependencies"],
    ))
    assert result is None

def test_http_client_write_invocation(async_sqlite_serializer: AsyncSQLiteSerializer):
    _app, client, *_ = create_test_app(async_sqlite_serializer)

    # Invocation depends on an lmp being written so write one first
    lmp_id = uuid4().hex

    client.write_lmp(WriteLMPInput(
        lmp_id=lmp_id,
        name="Test LMP",
        source="def test_function(): pass",
        dependencies=str(["dep1", "dep2"]),
        lmp_type=LMPType.LM,
    ))

    invocation_id = uuid4().hex
    result = client.write_invocation(WriteInvocationInput(
        invocation=Invocation(
            id=invocation_id,
            lmp_id=lmp_id,
            contents=InvocationContents(
                invocation_id=invocation_id,
                results=[Message(role='user', content="hello")]
            ),
            created_at=utc_now(),
            latency_ms=42.0,
        ),
        consumes=[]
    ))
    assert result is None


if __name__ == "__main__":
    pytest.main()
