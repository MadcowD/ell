===================
Structured Outputs
===================

Structured outputs allow for more controlled and predictable responses from language models.

.. code-block:: python

   from pydantic import BaseModel

   class MovieReview(BaseModel):
       title: str
       rating: int
       summary: str

   @ell.complex(model="gpt-4")
   def generate_movie_review(movie: str) -> MovieReview:
       # Implementation
       pass