from typing import Optional
from pydantic import BaseModel, Field
import ell
import requests

import ell.lmp.tool
from ell.lstr import lstr
from ell.stores.sql import SQLiteStore


@ell.tool()
def get_html_content(
    url : str = Field(description="The URL to get the HTML content of. Never incldue the protocol (like http:// or https://)"),
    ):
    """Get the HTML content of a URL."""
    return lstr(requests.get(url))


@ell.text(model="gpt-4o", tools=[get_html_content], eager=True)
def summarize_website(website :str) -> str:
    """You are an agent that can summarize the contents of a website."""
    return f"Tell me whats on {website}"


if __name__ == "__main__":
    ell.config.verbose = True
    ell.set_store(SQLiteStore("sqlite_example"), autocommit=True)
    f = summarize_website("nyt front page") # Message{[MessageContentBlock[function_call]]}