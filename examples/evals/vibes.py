import ell

from pydantic import BaseModel

class TweetInput(BaseModel):
    input: str

@ell.simple(model="gpt-4o")
def tweet(obj: TweetInput):
    print(obj)
    return f"Write a tweet like roon in lower case about {obj.input}"


dataset = [
{"input": [TweetInput(input="Polymath")]},
    {"input": [TweetInput(input="Dogs")]},
    {"input": [TweetInput(input="Intelligenve")]},
]


# # No metrics. We will iterate on by just looking at the output/
eval = ell.evaluation.Evaluation(
    name="vibes",
    dataset=dataset,
    criterion=lambda datapoint, output: "roon" in output.lower(),
)

if __name__ == "__main__":
    ell.init(store="./logdir", verbose=True)
    eval.run(tweet)
    # tweet("hi")
