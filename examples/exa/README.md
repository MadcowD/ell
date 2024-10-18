# Exa and ell Integration: Article Review Generator

This guide demonstrates how to integrate Exa's powerful search capabilities with ell's language model programming to create an article review generator focused on climate change.

## Prerequisites

Before you begin, make sure you have the following:

1. An Exa API key (Get it [here](https://docs.exa.ai/reference/getting-started-with-python))
2. An OpenAI API key
3. Python 3.7 or later installed

## Installation

Install the required packages:

```
pip install exa_py ell openai python-dotenv pydantic

```
## Setup

1. Create a `.env` file in your project directory with your API keys:

```
EXA_API_KEY=your_exa_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

2. Import the necessary libraries and load the environment variables:

```python
from exa_py import Exa
import ell
from openai import OpenAI
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json

load_dotenv()
```

3. Initialize the Exa and OpenAI clients:

```python
exa = Exa(os.getenv("EXA_API_KEY"))
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

## Defining the Article Review Structure

Use Pydantic to define the structure of the article review:

```python
class ArticleReview(BaseModel):
    title: str = Field(description="The title of the article")
    summary: str = Field(description="A summary of the article")
    rating: int = Field(description="A rating of the article from 1 to 10")
```

## Creating the Article Review Generator

Use ell to create a language model program for generating article reviews:

```python
@ell.complex(model="gpt-4o", client=openai, response_format=ArticleReview)
def generate_article_review(article: str, content: str) -> ArticleReview:
    """You are a article review generator. Given the name of an article, some content,
    you need to return a structured review"""
    return f"generate a review for the article {article} with content {content}"
```

## Implementing Exa Search

Create a function to search for climate change articles and return the results as a JSON object using Exa:

```python
def exa_search(num_results: int):
    result = exa.search_and_contents(
    "newest climate change articles",
    type="neural",
    use_autoprompt=True,
    start_published_date="2024-09-01",
    num_results=num_results,
    text=True,
    )
    json_data = json.dumps([result.__dict__ for result in result.results])
    return json.loads(json_data)
```

## Combining Exa Search and Article Review Generation

Create a RAG (Retrieval-Augmented Generation) function that combines Exa search results with the article review generator:

```python
def RAG(num_results: int):
    search_results = exa_search(num_results)
    for i in range(num_results):
        result = search_results[i]
        review = generate_article_review(result["title"], result["text"])
        print(review)
```

## Running the Article Review Generator

To generate reviews for the three most recent climate change articles:

```python
RAG(3)
```

This will print structured reviews for the three most recent climate change articles found by Exa.

## Conclusion

This integration demonstrates how to combine Exa's powerful search capabilities with ell's language model programming to create an automated article review generator. By leveraging Exa's ability to find recent, relevant articles and ell's structured output generation, you can quickly analyze and summarize the latest information on climate change or any other topic of interest.

For more information on Exa and ell, refer to their respective documentation:
- [Exa Documentation](https://docs.exa.ai/)
- [ell Documentation](https://docs.ell.so/)
