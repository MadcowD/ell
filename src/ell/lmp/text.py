from functools import wraps
from typing import Optional

import openai
from ell.lmp.multimodal import multimodal


@wraps(multimodal)
def text(model: str, client: Optional[openai.Client] = None,  exempt_from_tracking=False, **lm_kwargs):
    """a basic language model programming decorator for text only llm prompting."""
    assert 'tools' not in lm_kwargs, "tools are not supported in lm decorator, use multimodal decorator instead"
    assert 'tool_choice' not in lm_kwargs, "tool_choice is not supported in lm decorator, use multimodal decorator instead"
    assert 'response_format' not in lm_kwargs, "response_format is not supported in lm decorator, use multimodal decorator instead"

    def convert_multimodal_response_to_lstr(response):
        return [x.content[0].text for x in response] if isinstance(response, list) else response.content[0].text
    return multimodal(model, client,  exempt_from_tracking, **lm_kwargs, post_callback=convert_multimodal_response_to_lstr)


