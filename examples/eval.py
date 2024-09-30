import ell
import ell.evaluation

dataset = [
    ("What is the capital of france?", "Paris"),
    ("What is the capital of italy?", "Rome"),
    ("What is the capital of spain?", "Madrid"),
    ("What is the capital of germany?", "Berlin"),
    ("What is the capital of japan?", "Tokyo"),
    ("What is the capital of china?", "Beijing"),
    ("What is the capital of india?", "New Delhi"),
    ("What is the capital of brazil?", "Brasília"),
    ("What is the capital of argentina?", "Buenos Aires"),
    ("Hotdog land", "Hotdog land"),
]

def is_correct(datapoint, output):
    label = datapoint[1]
    return output.lower() == label.lower()

eval = ell.evaluation.Evaluation(name= "test",dataset=dataset, metric=is_correct)
# ell.init(verbose=True, store='./logdir')
@ell.simple(model="gpt-4o")
def predict_capital(question: str):
    """
    Answer only with the capital of the country.
    """
    # print(question[0])
    return f"Answer the following question. {question[0]}"

result = eval.run(predict_capital, n_workers=4)
print(result.outputs)

# Would be cool if it opened a UI for you to watch the run as it was going down.