#!/usr/bin/env python3

# Educational Example: Using LLM with Wikipedia Tools
#
# This script demonstrates how to use an LLM agent with tools to interact with Wikipedia.
# It provides two main functionalities:
# * Searching Wikipedia for relevant pages.
# * Fetching and reading the content of a Wikipedia page.
#
# The script uses `lynx --dump` to obtain a textual representation of web pages.
#
# Workflow:
# 1. The AI agent searches Wikipedia based on user queries and suggests a page to read.
#     * Agent keeps searching, trying different kewords, until sees some promising result.
# 2. The agent uses tool to read the page content to answer the user's query.
#
# This example is designed to be educational and is suitable for inclusion in an `examples/` directory.
# It illustrates the integration of LLMs with external tools to perform complex tasks.
#
# For those interested in understanding the inner workings, try running the script with the `-v` or `-vv` flags.
# These flags will provide additional insights into the process and can be very helpful for learning purposes.
#
# Bonus Task: Consider looking at `llm_lottery.py` which uses `loop_llm_and_tools` to allow the LLM to call tools
# as long as needed to accomplish a task. Think about how you might modify this script to search and read Wikipedia
# pages until it knows enough to provide a sufficient response to a query, such as a comparison between multiple cities.
# (spoiler, example solution: https://gist.github.com/gwpl/27715049d41ec829f21014f3b243850a )

import argparse
import subprocess
import sys
from functools import partial
import urllib.parse

import ell
from ell import Message
from pydantic import Field

eprint = partial(print, file=sys.stderr)

VERBOSE = False

@ell.tool(strict=True)
def search_wikipedia(keywords: str = Field(description="Kewords for wikipedia search engine.")):
    """Search Wikipedia and return a list of search results and links."""
    if VERBOSE:
        eprint(f"Calling tool: search_wikipedia('{keywords}')")
        
    encoded_query = urllib.parse.quote(keywords)
    cmd = f"lynx --dump 'https://en.m.wikipedia.org/w/index.php?search={encoded_query}'"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout.decode('ISO-8859-1')[:65536]

@ell.tool(strict=True)
def wikipedia_page_content(wiki_page_url: str):
    """Fetch the content of a Wikipedia page given its URL."""
    if VERBOSE:
        eprint(f"Calling tool: wikipedia_page_content('{wiki_page_url}')")
        
    cmd = f"lynx --dump '{wiki_page_url}'"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    return result.stdout.decode('ISO-8859-1')[:65536]

@ell.complex(model="gpt-4o-mini", tools=[search_wikipedia])
def search_wikipedia_and_suggest_page_to_read(message_history: list[Message]) -> list[Message]:
    if VERBOSE:
        last_msg = message_history[-1].text
        if len(last_msg) > 100:
            last_msg = last_msg[:100] + "..."
        eprint(f"Calling LMP: search_wikipedia_and_suggest_page_to_read('{last_msg}')")
    return [
        ell.system("You are an AI assistant that searches Wikipedia and suggests URL of wikipedia page to read. Return ONLY URL. Call tool that takes keywords for Wikipedia search engine, to get wikipedia search engine results. Based on results suggest one best, most promisting/relevent URL to read.")
    ] + message_history

@ell.complex(model="gpt-4o", tools=[wikipedia_page_content])
def answer_query_by_reading_wikipedia_page(message_history: list[Message]) -> list[Message]:
    if VERBOSE:
        last_msg = message_history[-1].text
        eprint(f"Calling LMP: answer_query_by_reading_wikipedia_page({last_msg})")
    return [
        ell.system("You are an AI assistant that reads a Wikipedia page and provides answers based on the information found. Read the content of the Wikipedia page at provided URL. Call tool to fetch content of page. Use the content to provide a comprehensive answer to user query. Include quotes on which answer is based on.")
    ] + message_history

def loop_llm_and_tools(f, message_history, max_iterations=10):
    iteration = 0
    while iteration < max_iterations:
        response_message = f(message_history)
        message_history.append(response_message)

        if response_message.tool_calls:
            tool_call_response = response_message.call_tools_and_collect_as_message()
            message_history.append(tool_call_response)
        else:
            break
        iteration += 1
    return message_history

def main():
    parser = argparse.ArgumentParser(description='Search Wikipedia and answer questions.')
    parser.add_argument('query', type=str, help='The query to search for on Wikipedia')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity level')
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose > 0

    ell.init(verbose=(args.verbose > 1), store='./logdir', autocommit=True)

    if args.verbose > 0:
        eprint(f"Provided Query: {args.query}")

    message_history = []
    message_history.append(ell.user(args.query))

    if args.verbose > 1:
        eprint(f"message_history as early stage = {message_history}")

    message_history = loop_llm_and_tools(search_wikipedia_and_suggest_page_to_read, message_history)

    url = message_history[-1].text
    eprint(f"Intermediate Result: {url}")

    message_history = loop_llm_and_tools(answer_query_by_reading_wikipedia_page, message_history)

    eprint("Result:")
    print(f"{message_history[-1].text}\n")

if __name__ == "__main__":
    main()


# This script does the following:
#
# 1. Defines two tools: `search_wikipedia` and `wikipedia_page_content` using the `@ell.tool()` decorator.
#    These tools use the `lynx` command-line browser to fetch search results and page content from Wikipedia.
#
# 2. Implements two complex functions using the `@ell.complex` decorator:
#    - `search_wikipedia_and_suggest_page_to_read`: Searches Wikipedia and suggests a page URL.
#    - `answer_query_by_reading_wikipedia_page`: Reads a Wikipedia page and answers the user's query.
#
# 3. The `main` function sets up argument parsing, initializes ell with the appropriate verbosity, and manages the
#    interaction loop using `loop_llm_and_tools` to process the query and fetch results.
#
# 4. The script supports two levels of verbosity:
#    - With `-v`, it prints progress information to stderr.
#    - With `-vv`, it also enables verbosity for ell.init.
#
# 5. Finally, it prints the intermediate URL result and the final answer based on the Wikipedia page content.
#
# To use this script, you would run it from the command line like this:
#
# ```
# python3 wikipedia_mini_rag.py "Your query here" -v
# ```
#
# Make sure you have the `lynx` command-line browser installed on your system for this script to work properly.
