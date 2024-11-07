import * as logging from 'ell-ai/util/_logging'
logging.setGlobalLevel(logging.LogLevel.DEBUG)
import * as ell from 'ell-ai'
import { z } from 'zod'

const MovieReview = z.object({
  title: z.string().describe("The title of the movie"),
  rating: z.number().int().describe("The rating of the movie out of 10"),
  summary: z.string().describe("A brief summary of the movie")
})

const generateMovieReview = ell.complex({ 
  model: "gpt-4o-mini", 
  response_format: MovieReview ,
}, (movie: string) => {
  return [
    ell.system("You are a movie review generator. Given the name of a movie, you need to return a structured review."),
    ell.user(`Generate a review for the movie ${movie}`)
  ]
})

;(async () => {
  ell.init({ store: './logdir', autocommit: true, verbose: true })

  const reviewMessage = await generateMovieReview("The Matrix")
  console.log(reviewMessage)
  const review = reviewMessage.parsed

  console.log(`Movie: ${review.title}, Rating: ${review.rating}/10`)
  console.log(`Summary: ${review.summary}`)
})()