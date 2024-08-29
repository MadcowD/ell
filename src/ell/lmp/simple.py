from functools import wraps
from typing import Optional

import openai
from ell.lmp.complex import complex


@wraps(complex)
def simple(model: str, client: Optional[openai.Client] = None,  exempt_from_tracking=False, **api_params):
    """a basic language model programming decorator for text only llm prompting."""
    assert 'tools' not in api_params, "tools are not supported in lm decorator, use multimodal decorator instead"
    assert 'tool_choice' not in api_params, "tool_choice is not supported in lm decorator, use multimodal decorator instead"
    assert 'response_format' not in api_params, "response_format is not supported in lm decorator, use multimodal decorator instead"

    def convert_multimodal_response_to_lstr(response):
        return [x.content[0].text for x in response] if isinstance(response, list) else response.content[0].text
    return complex(model, client,  exempt_from_tracking, **api_params, post_callback=convert_multimodal_response_to_lstr)


