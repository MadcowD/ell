from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Type
from ell.provider import APICallResult, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
from ell.types.message import LMP
from ell.configurator import register_provider

try:
    import cohere

    class CohereProvider(Provider):
        @staticmethod
        def content_block_to_cohere_format(content_block: ContentBlock) -> Dict[str, Any]:
            if content_block.text:
                return content_block.text
            elif content_block.parsed:
                return content_block.parsed.model_dump_json()
            # If Cohere support images we can add it here
            return None

        @staticmethod
        def message_to_cohere_format(message: Message) -> Dict[str, str]:
            content = " ".join(filter(None, [
                CohereProvider.content_block_to_cohere_format(c) for c in message.content
            ]))
            return {
                "role": message.role,
                "message": content
            }

        @classmethod
        def call_model(
            cls,
            client: Any,
            model: str,
            messages: List[Message],
            api_params: Dict[str, Any],
            tools: Optional[list[LMP]] = None,
        ) -> APICallResult:
            final_call_params = api_params.copy()

            cohere_messages = [cls.message_to_cohere_format(message) for message in messages]
            
            user_message = cohere_messages[-1]["message"] if cohere_messages else ""
            chat_history = cohere_messages[:-1] if len(cohere_messages) > 1 else None
            
            actual_n = api_params.get("n", 1)

            chat_params = {
                "message": user_message,
                "model": model,
                "chat_history": chat_history,
                "max_tokens": final_call_params.get("max_tokens"),
                "temperature": final_call_params.get("temperature", 0.7),
            }
            
            if tools:
                # This is a placeholder for future implementation
                pass

            response = client.chat(**chat_params)

            return APICallResult(
                response=response,
                actual_streaming=False,
                actual_n=actual_n,
                final_call_params=chat_params,
            )

        @classmethod
        def process_response(
            cls, call_result: APICallResult, _invocation_origin: str, logger: Optional[Any] = None, tools: Optional[List[LMP]] = None,
        ) -> Tuple[List[Message], Dict[str, Any]]:
            choices_progress = defaultdict(list)
            metadata = {}
            
            if not call_result.actual_streaming:
                response = [call_result.response]
            else:
                response = call_result.response

            for chunk in response:
                if hasattr(chunk, "meta"):
                    metadata["usage"] = {
                        "prompt_tokens": chunk.meta.tokens.input_tokens,
                        "completion_tokens": chunk.meta.tokens.output_tokens,
                        "total_tokens": chunk.meta.tokens.input_tokens + chunk.meta.tokens.output_tokens,
                    }

                choices_progress[0].append(chunk)
                if logger:
                    logger(chunk.text if call_result.actual_streaming else chunk.text)
               
                
            tracked_results = []
            for _, choice_deltas in sorted(choices_progress.items(), key=lambda x: x[0]):
                content = []

                if call_result.actual_streaming:
                    text_content = "".join(
                        (choice.text or "" for choice in choice_deltas)
                    )
                else:
                    text_content = choice_deltas[0].text

                if text_content:
                    content.append(
                        ContentBlock(
                            text=_lstr(
                                content=text_content, _origin_trace=_invocation_origin
                            )
                        )
                    )
                
                tracked_results.append(
                    Message(
                        role="assistant",
                        content=content,
                    )
                )

            return tracked_results, metadata

        @classmethod
        def supports_streaming(cls) -> bool:
            return False

        @classmethod
        def get_client_type(cls) -> Type:
            return cohere.Client

    register_provider(CohereProvider)

except ImportError:
    pass