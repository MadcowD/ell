from exa_py import Exa
import ell
from openai import OpenAI
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json

load_dotenv()
exa = Exa(os.getenv("EXA_API_KEY"))

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ArticleReview(BaseModel):
    title: str = Field(description="The title of the article")
    summary: str = Field(description="A summary of the article")
    rating: int = Field(description="A rating of the article from 1 to 10")

@ell.complex(model="gpt-4o", client=openai, response_format=ArticleReview)
def generate_article_review(article: str, content: str) -> ArticleReview:
    """You are a article review generator. Given the name of an article, some content,
    you need to return a structured review"""
    return f"generate a review for the article {article} with content {content}"

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


def RAG(num_results: int):
    search_results = exa_search(num_results)
    for i in range(num_results):
        result = search_results[i]
        review = generate_article_review(result["title"], result["text"])
        print(review)

RAG(3)





