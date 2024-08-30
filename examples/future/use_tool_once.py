from typing import Optional
from pydantic import BaseModel, Field
import ell
import requests

import openai


import ell.lmp.tool
from ell.types._lstr import _lstr
from ell.stores.sql import SQLiteStore

ell.config.verbose = True
ell.set_store(SQLiteStore("./logdir"), autocommit=True)

from bs4 import BeautifulSoup

@ell.tool()
def get_html_content(
    url : str = Field(description="The URL to get the HTML content of. Never incldue the protocol (like http:// or https://)"),
    ):
    """Get the HTML content of a URL."""
    response = requests.get("https://" + url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # print(soup.get_text())~
    return soup.get_text()[:100]


@ell.complex(model="gpt-4o", tools=[get_html_content])
def summarize_website(website :str) -> str:
    """You are an agent that can summarize the contents of a website."""
    return f"Tell me whats on {website}"


if __name__ == "__main__":
    output = summarize_website("langchains website") # Message{[MessageContentBlock[function_call]]}
    print(output)
    if output.tool_calls:
        tool_results = output.call_tools_and_collect_as_message()

    print(tool_results)
    # print(output)
   

    

