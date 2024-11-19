# you'll need to install sklearn as its not a dependency of ell
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from ell import ell


class VectorStore:
    def __init__(self, vectorizer, tfidf_matrix, documents):
        self.vectorizer = vectorizer
        self.tfidf_matrix = tfidf_matrix
        self.documents = documents

    @classmethod
    def from_documents(cls, documents):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)
        return cls(vectorizer, tfidf_matrix, documents)

    def search(self, query: str, k: int = 2) -> list[dict]:
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        return [
            {"document": self.documents[i], "relevan": float(similarities[i])}
            for i in top_k_indices
        ]


@ell.simple(model="gpt-4o-mini")
def rag(query: str, context: str) -> str:
    """You are an AI assistant using Retrieval-Augmented Generation (RAG).
    RAG enhances your responses by retrieving relevant information from a knowledge base.
    You will be provided with a query and relevant context. Use this context to inform your response,
    but also draw upon your general knowledge when appropriate.
    Always strive to provide accurate, helpful, and context-aware answers."""

    return f"""
    Given the following query and relevant context, please provide a comprehensive and accurate response:

    Query: {query}

    Relevant context:
    {context}

    Response:
    """


if __name__ == "__main__":
    

    documents = [
        "ell is a cool new framework written by will",
        "will writes a lot of the code while on x.com the everything app",
        "ell will someday be go-to tool for getting things done",
        "george washington is the current president of the United states of America",
    ]

    vector_store = VectorStore.from_documents(documents)

    query = "who created ell?"
    context = vector_store.search(query)

    question1 = rag(query, context)

    query = "who is the president of america?"
    context = vector_store.search(query)

    question2 = rag(query, context)
