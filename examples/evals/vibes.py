import ell

@ell.simple(model="gpt-4o")
def tweet(text: str):
    return f"Write a tweet like roon in lower case about {text}"


dataset = [
    {
        "input": "Polymath",
    },
    {
        "input": "Dogs",
    },
    {
        "input": "Intelligenve",
    }
]


# # No metrics. We will iterate on by just looking at the output/
# eval = ell.evaluation.Evaluation(
#     name="vibes",
#     dataset=dataset,
# )

if __name__ == "__main__":
    ell.init(store="./logdir", verbose=True)
    tweet("hi")
