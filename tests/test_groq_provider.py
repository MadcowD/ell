# src/ell/providers/groq.py

from typing import Any, Dict, List, Optional, Tuple, Type
from ell.provider import APICallResult, Provider
from ell.types import Message, ContentBlock, ToolCall
from ell.types._lstr import _lstr
from ell.configurator import register_provider, config
import json
import logging
import os

logger = logging.getLogger(__name__)

try:
    from groq import Groq

    class GroqProvider(Provider):
        @classmethod
        def call_model(
            cls,
            client: Groq,
            model: str,
            messages: List[Message],
            api_params: Dict[str, Any],
            tools: Optional[List[Any]] = None,
        ) -> APICallResult:
            logger.debug(f"call_model called with client: {client}")
            if client is None:
                logger.error("Groq client is None in call_model.")
                raise ValueError("Groq client is not initialized.")

            logger.debug(f"Model: {model}")
            logger.debug(f"API Params: {api_params}")
            logger.debug(f"Messages: {messages}")

            try:
                # Convert and prepare messages
                groq_messages = [cls.message_to_groq_format(message) for message in messages]
                logger.debug(f"Converted messages for Groq: {groq_messages}")

                # Prepare final call parameters
                final_call_params = api_params.copy()
                final_call_params["model"] = model
                final_call_params["messages"] = groq_messages
                logger.debug(f"Final call parameters: {final_call_params}")

                # Make the API call
                response = client.chat.completions.create(**final_call_params)
                logger.debug(f"Received response from Groq: {response}")

                return APICallResult(
                    response=response,
                    actual_streaming=True,  # Adjust based on Groq's actual behavior
                    actual_n=api_params.get("n", 1),
                    final_call_params=final_call_params,
                )
            except Exception as e:
                logger.error(f"Exception during call_model: {e}")
                raise e

        @classmethod
        def process_response(
            cls,
            call_result: APICallResult,
            _invocation_origin: str,
            func_logger: Optional[Any] = None,  # Renamed to avoid shadowing
            tools: Optional[List[Any]] = None,
        ) -> Tuple[List[Message], Dict[str, Any]]:
            logger.debug("Processing Groq response.")
            try:
                tracked_results = []
                metadata = {}

                # Correctly access the 'choices' attribute
                choices = call_result.response.choices
                if not choices:
                    raise ValueError("No choices found in Groq response.")

                for choice in choices:
                    # Correctly access 'message' and 'content'
                    content = choice.message.content
                    if not content:
                        logger.warning("Empty content in Groq response choice.")
                        continue

                    tracked_results.append(
                        Message(
                            role="assistant",
                            content=[ContentBlock(text=_lstr(content, _origin_trace=_invocation_origin))]
                        )
                    )
                    logger.debug(f"Tracked results: {tracked_results}")

                logger.debug(f"Metadata: {metadata}")

                return tracked_results, metadata
            except Exception as e:
                logger.error(f"Error processing Groq response: {e}")
                raise e

        @classmethod
        def supports_streaming(cls) -> bool:
            streaming_support = True  # Adjust if Groq doesn't support streaming
            logger.debug(f"supports_streaming: {streaming_support}")
            return streaming_support

        @classmethod
        def get_client_type(cls) -> Type:
            api_key = os.environ.get("GROQ_API_KEY")
            logger.debug(f"GROQ_API_KEY retrieved: {api_key is not None}")
            return Groq

        @staticmethod
        def message_to_groq_format(message: Message) -> Dict[str, Any]:
            # Convert ell Message to Groq format
            if any(block.parsed for block in message.content):
                # Handle parsed content blocks
                parsed_contents = [
                    json.dumps(block.parsed.model_dump(), separators=(',', ':')) if block.parsed else block.text
                    for block in message.content
                ]
                # Concatenate all content blocks with a newline
                content = "\n".join(parsed_contents)
            else:
                # Handle text content blocks
                content = message.text

            groq_format = {
                "role": message.role,
                "content": content
            }
            logger.debug(f"Converted message to Groq format: {groq_format}")
            return groq_format

    # Register the GroqProvider
    register_provider(GroqProvider)
    logger.info("GroqProvider registered successfully.")
    print("[GroqProvider] GroqProvider registered successfully.")

except ImportError:
    logger.warning("Groq package not found. Groq provider will not be available.")
    print("[GroqProvider] ImportError: Groq package not found.")

    def get_groq_client():
        raise ImportError("Groq package is not installed. Unable to create Groq client.")
