import ell
import time
import ell.evaluation

ell.init(verbose=True, store="./logdir")

@ell.simple(model="gpt-4o")
def write_a_bad_poem():
    """Use long words. Your poem should be no longer than 70 words."""
    return "Write a really poorly written poem "

@ell.simple(model="gpt-4o")
def write_a_good_poem():
    """Make your poems about 60 words long."""
    return "Write a really well written poem."

@ell.simple(model="gpt-4o", temperature=0.1)
def is_good_poem(poem: str):
    """Include either 'yes' or 'no' at the end of your response. <analysis>. <yes or no>."""
    return f"Is this a good poem yes/no? {poem}"

def score(datapoint, output):
    return "yes" in is_good_poem(output).lower()

ell.init(verbose=True, store="./logdir")

eval = ell.evaluation.Evaluation(
    name="poem_eval",
    n_evals=100,
    metrics={
        "critic_score": score,
        "length": lambda _, output: len(output),
        "average_word_length": lambda _, output: sum(
            len(word) for word in output.split()
        )
        / len(output.split()),
    },
)

print("EVALUATING GOOD POEM")
start = time.time()
# run = eval.run(write_a_good_poem, n_workers=10, verbose=False)
# print(f"Average length: {run.results.metrics['length'].mean():.2f}")
# print(f"Average word length: {run.results.metrics['average_word_length'].mean():.2f}")
# print(f"Average critic score: {run.results.metrics['critic_score'].mean():.2f}")
# print(f"Time taken: {time.time() - start:.2f} seconds")
# print("EVALUATING BAD POEM")
run = eval.run(write_a_bad_poem, n_workers=10, verbose=False)
print(f"Average length: {run.results.metrics['length'].mean():.2f}")
print(
    f"Average word length: {run.results.metrics['average_word_length'].mean():.2f}"
)
print(f"Average critic score: {run.results.metrics['critic_score'].mean():.2f}")
