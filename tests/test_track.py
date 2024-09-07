from typing import Any, Dict, List, Optional
import openai
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.pytest_plugin import register_fixture
from pytest_mock import MockerFixture


import ell
import pytest
from ell.api.client import EllAPIClient, EllClient, EllSqliteClient
from ell.api.types import LMP, GetLMPResponse, WriteInvocationInput, WriteLMPInput

from ell.stores.sql import SQLStore, SQLiteStore


# T = TypeVar('T')

# class SpyWrapper:
#     def __init__(self, original_method: Callable, spy_method: Any):
#         self.original_method = original_method
#         self.spy_method = spy_method

#     def __call__(self, *args: Any, **kwargs: Any) -> Any:
#         return self.spy_method(*args, **kwargs)

#     def __getattr__(self, name: str) -> Any:
#         return getattr(self.spy_method, name)

# class SpiedObject(Generic[T]):
#     def __init__(self, original: T):
#         self._original = original

#     def __getattr__(self, name: str) -> Any:
#         return getattr(self._original, name)

# def spy_all_methods(mocker: MockerFixture, obj: T) -> SpiedObject[T]:
#     spied_obj = SpiedObject(obj)
#     for attr_name in dir(obj):
#         attr = getattr(obj, attr_name)
#         if callable(attr) and not attr_name.startswith('__'):
#             spy = mocker.spy(obj, attr_name)
#             setattr(spied_obj, attr_name, SpyWrapper(attr, spy))
#     return spied_obj


@pytest.fixture
def sql_store() -> SQLStore:
    return SQLiteStore(":memory:")


@pytest.fixture
def mock_openai_chatcompletion(monkeypatch: pytest.MonkeyPatch):

    class AsyncChatCompletionIterator:
        def __init__(self, answer: str):
            self.answer_index = 0
            self.answer_deltas = answer.split(" ")

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.answer_index < len(self.answer_deltas):
                answer_chunk = self.answer_deltas[self.answer_index]
                self.answer_index += 1
                return openai.util.convert_to_openai_object(
                    {"choices": [{"delta": {"content": answer_chunk}}]})
            else:
                raise StopAsyncIteration

    async def mock_acreate(*args, **kwargs):
        return AsyncChatCompletionIterator("The capital of France is Paris.")

    monkeypatch.setattr(openai.ChatCompletion, "create", mock_acreate)

    def mock_create(*args, **kwargs):
        return [ChatCompletion(
            id="chatcmpl-123",
            object="chat.completion",
            created=1677652288,
            model="gpt-3.5-turbo",
            choices=[Choice(
                index=0,
                finish_reason='stop',
                message=ChatCompletionMessage(role="assistant", content="Hello!"))],
            usage=CompletionUsage(
                prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )]

    class MockCompletions:
        def create(*args, **kwargs):
            return mock_create(*args, **kwargs)

    class MockChat:
        def __init__(self, *args, **kwargs):
            self.completions = MockCompletions()

    class MockOpenAPIClient:
        def __init__(self, *args, **kwargs):
            self.api_key = "test-api-key"
            self.chat = MockChat()

    # monkeypatch.setattr(openai.chat.completions, "create", mock_create)
    return MockOpenAPIClient(api_key="test-api-key")


def test_track_decorator_sqlite(mock_openai_chatcompletion: openai.Client):
    ell.config.register_model(model_name="test-model",
                              client=mock_openai_chatcompletion)
    ell.init(client=EllSqliteClient(storage_dir=':memory:'))

    @ell.simple(model="test-model")
    def test_fn():
        return f"this is a test"

    test_fn()


@register_fixture
class LMPFactory(ModelFactory[LMP]):
    ...


def test_track_decorator_api(
    mocker: MockerFixture,
    mock_openai_chatcompletion: openai.Client,
    lmp_factory: LMPFactory
):
    ell.config.register_model(model_name="test-model",
                              client=mock_openai_chatcompletion)

    ell.config.register_model(model_name='gpt-4o-mini',
                              client=mock_openai_chatcompletion)

    class TestAPIClient(EllClient):
        def __init__(self, base_url: str):
            self.base_url = base_url

        async def get_lmp(self, lmp_id: str) -> GetLMPResponse:
            lmp = lmp_factory.build()
            lmp.id = lmp_id
            return lmp

        async def get_lmp_versions(self, fqn: str) -> List[LMP]:
            lmp = lmp_factory.build()
            lmp.name = fqn
            return [lmp_factory.build()]

        async def write_lmp(self, lmp: WriteLMPInput, uses: List[str]):
            return None

        async def write_invocation(self, input: WriteInvocationInput):
            return None
        
        async def store_blob(self, blob: bytes, metadata: Optional[Dict[str, Any]] = None) -> str:
            return "foo"

        async def retrieve_blob(self, blob_id: str) -> bytes:
            return b"bar"

        async def close(self):
            pass

    api_client = TestAPIClient(base_url="foo")
    get_lmp_versions = mocker.spy(api_client, "get_lmp_versions")
    write_lmp = mocker.spy(api_client, "write_lmp")
    write_invocation = mocker.spy(api_client, "write_invocation")

    ell.init(client=api_client)

    @ell.simple(model="test-model")
    def test_fn():
        return f"this is a test"

    test_fn()

    assert get_lmp_versions.call_count == 1
    assert write_lmp.call_count == 1
    assert write_invocation.call_count == 1


if __name__ == "__main__":
    pytest.main()
