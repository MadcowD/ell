from collections import UserDict
from types import NoneType
from typing import Any, Dict, Iterable, Optional, Protocol, List, Union
import ell
import ell.evaluation
import numpy as np


def test_predictor_evaluation():
    dataset: List[ell.evaluation.Datapoint] = [
        {
            "input": {"question": "What is the capital of france?"},
            "expected_output": "Paris",
        },
        {
            "input": {"question": "What is the capital of italy?"},
            "expected_output": "Rome",
        },
        {
            "input": {"question": "What is the capital of spain?"},
            "expected_output": "Madrid",
        },
        {
            "input": {"question": "What is the capital of germany?"},
            "expected_output": "Berlin",
        },
        {
            "input": {"question": "What is the capital of japan?"},
            "expected_output": "Tokyo",
        },
        {
            "input": {"question": "What is the capital of china?"},
            "expected_output": "Beijing",
        },
        {
            "input": {"question": "What is the capital of india?"},
            "expected_output": "New Delhi",
        },
        {
            "input": {"question": "What is the capital of brazil?"},
            "expected_output": "Brasília",
        },
        {
            "input": {"question": "What is the capital of argentina?"},
            "expected_output": "Buenos Aires",
        },
        {"input": {"question": "Hotdog land"}, "expected_output": "Hotdog land"},
    ]

    def is_correct(datapoint, output):
        label = datapoint["expected_output"]
        return float(output.lower() == label.lower())

    eval = ell.evaluation.Evaluation(
        name="test", dataset=dataset, criteria={"score": score, "length": lambda _, output: len(output)}
    )

    # ell.init(verbose=True, store='./logdir')
    @ell.simple(model="gpt-4o")
    def predict_capital(question: str):
        """
        Answer only with the capital of the country. If hotdog land, answer hotdog land.
        """
        # print(question[0])
        return f"Answer the following question. {question}"

    result = eval.run(predict_capital, n_workers=4)
    print(result.scores.mean())


# def test_llm_critic_evaluation():
dataset: List[ell.evaluation.Datapoint] = [
    {
        "input": {  # I really don't like this. Forcing "input" without typing feels disgusting.
            "text": "The Industrial Revolution was a period of major industrialization and innovation that took place during the late 1700s and early 1800s. It began in Great Britain and quickly spread throughout Western Europe and North America. This revolution saw a shift from an economy based on agriculture and handicrafts to one dominated by industry and machine manufacturing. Key technological advancements included the steam engine, which revolutionized transportation and manufacturing processes. The textile industry, in particular, saw significant changes with the invention of spinning jennies, water frames, and power looms. These innovations led to increased productivity and the rise of factories. The Industrial Revolution also brought about significant social changes, including urbanization, as people moved from rural areas to cities for factory work. While it led to economic growth and improved living standards for some, it also resulted in poor working conditions, child labor, and environmental pollution. The effects of this period continue to shape our modern world."
        },
        "expected_output": "A comprehensive summary of the Industrial Revolution",
    },
    {
        "input": {
            "text": "The human genome is the complete set of nucleic acid sequences for humans, encoded as DNA within the 23 chromosome pairs in cell nuclei and in a small DNA molecule found within individual mitochondria. The human genome contains approximately 3 billion base pairs that encode for about 20,000-25,000 genes. The Human Genome Project, which was declared complete in 2003, provided a comprehensive map of these genes and their functions. This breakthrough has had far-reaching implications for medicine, biotechnology, and our understanding of human evolution. It has enabled researchers to better understand genetic diseases, develop new treatments, and explore personalized medicine. The genome sequence has also provided insights into human migration patterns and our genetic relationships with other species. Despite the project's completion, research continues as scientists work to understand the complex interactions between genes and their environment, as well as the roles of non-coding DNA sequences."
        },
        "expected_output": "A detailed summary of the human genome and its significance",
    },
    {
        "input": {
            "text": "Climate change refers to long-term shifts in global weather patterns and average temperatures. Scientific evidence shows that the Earth's climate has been warming at an unprecedented rate since the mid-20th century, primarily due to human activities. The main driver of this change is the increased emission of greenhouse gases, particularly carbon dioxide, from burning fossil fuels, deforestation, and industrial processes. These gases trap heat in the Earth's atmosphere, leading to global warming. The effects of climate change are wide-ranging and include rising sea levels, more frequent and severe weather events (such as hurricanes, droughts, and heatwaves), changes in precipitation patterns, and disruptions to ecosystems. These changes pose significant threats to biodiversity, food security, water resources, and human health. Addressing climate change requires global cooperation to reduce greenhouse gas emissions through the adoption of clean energy technologies, sustainable land use practices, and changes in consumption patterns. Adaptation strategies are also necessary to help communities and ecosystems cope with the impacts that are already occurring or are inevitable."
        },
        "expected_output": "A comprehensive overview of climate change, its causes, effects, and potential solutions",
    },
    {
        "input": {
            "text": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The field of AI research was founded on the assumption that human intelligence can be precisely described and simulated by a machine. This concept has evolved significantly since its inception in the 1950s. Modern AI encompasses a wide range of capabilities, including problem-solving, learning, planning, natural language processing, perception, and robotics. Machine Learning, a subset of AI, focuses on the development of algorithms that can learn from and make predictions or decisions based on data. Deep Learning, a further specialization, uses artificial neural networks inspired by the human brain to process data and create patterns for decision making. AI has applications across numerous fields, including healthcare (for diagnosis and treatment recommendations), finance (for fraud detection and algorithmic trading), transportation (in the development of self-driving cars), and personal assistance (like Siri or Alexa). As AI continues to advance, it raises important ethical and societal questions about privacy, job displacement, and the potential for AI to surpass human intelligence in certain domains."
        },
        "expected_output": "A comprehensive explanation of Artificial Intelligence, its subfields, applications, and implications",
    },
]


@ell.simple(model="gpt-4o", temperature=0.1)
def critic(text_to_summarize: str, ai_produced_summary: str):
    """
        You are a critic of summaries. You are given a text and a summary of that text. You should evaluate the summary for how well it captures the main points of the text.

    Criterion:
    - Summary should be shorter than the original text. Do not give it a score above 50 if it is longer.
    - The best scoring summaries should be one sentence.
    - Summary should capture the main points of the text
    - Summary should be accurate
    - Summary should be concise

        Return a score between 0 and 100 for how well the summary captures the main points of the text. Your answer should be in the following format:
        Analysis:\\n<analysis of quality>\\nScore:\\n<score>
    """

    return f"""Text to summarize:
    {text_to_summarize}
    
    Summary:
    {ai_produced_summary}
    """


# model output etc. is just the second argument
# XXX: Need to support failure modes in metric computation...
import ell.lmp.function


@ell.lmp.function.function()
def score(datapoint, output, n_retries=3):
    for _ in range(n_retries):
        try:
            critique = critic(datapoint["input"]["text"], output)
            # print(critique)
            score = int(critique.split("Score:")[1].strip())
            return score
        except Exception as e:
            print(f"Error: {e}")
            continue
    raise Exception("Failed to score")


# named criteria are interesting, allows anonymous functions &  specific isntantiation of functional criteria (partial(...))
eval = ell.evaluation.Evaluation(
    name="test",
    dataset=dataset,
    criteria={"score": score, "length": lambda _, output: len(output)},
)
# this means
# we get metrics like "test-score", test-length etc.


# Now we prompt shit
@ell.simple(model="gpt-4o")
def summarizer(text: str):
    """You are a succinct summarizer. You are given a text and you should return a summary of the text. It should be no longer than 5 sentence. Focus on capturing the main points of the text as best as possible"""
    return f"Summarize the following text. {text}"


ell.init(verbose=True, store="./logdir")


# Using GPT-4o
print("EVAL WITH GPT-4o")
result = eval.run(summarizer, samples_per_datapoint=1, n_workers=4, verbose=True)
print(result.scores)
print("Mean critic score:", np.mean([s['score'] for s in result.scores]))
print("Mean length of completions:", np.mean([s['length'] for s in result.scores]))

# Using gpt-4o-mini
print("EVAL WITH GPT-4o-mini")
result = eval.run(
    summarizer,
    samples_per_datapoint=1,
    n_workers=1,
    api_params={"model": "gpt-4o-mini"},
    verbose=False,
)
print(result.scores)
print("Mean critic score:", np.mean([s['score'] for s in result.scores]))
print("Mean length of completions:", np.mean([s['length'] for s in result.scores]))

# Define named functions for criteria
def score_criterion(datapoint, output, n_retries=3):
    for _ in range(n_retries):
        try:
            critique = critic(datapoint["input"]["text"], output)
            score = int(critique.split("Score:")[1].strip())
            return score
        except Exception as e:
            print(f"Error: {e}")
            continue
    raise Exception("Failed to score")

def length_criterion(_, output):
    return len(output)

# Example using a list of criteria
eval_list = ell.evaluation.Evaluation(
    name="test_list",
    dataset=dataset,
    criteria=[score_criterion, length_criterion],
)

# Example using a dictionary of criteria (as before)
eval_dict = ell.evaluation.Evaluation(
    name="test_dict",
    dataset=dataset,
    criteria={"score": score_criterion, "length": length_criterion},
)

# Run evaluation with list-based criteria
print("EVAL WITH GPT-4o (list-based criteria)")
result_list = eval_list.run(summarizer, samples_per_datapoint=1, n_workers=4, verbose=False)
print(result_list.scores)
print("Mean critic score:", np.mean([s['score_criterion'] for s in result_list.scores]))
print("Mean length of completions:", np.mean([s['length_criterion'] for s in result_list.scores]))

# Run evaluation with dict-based criteria
print("EVAL WITH GPT-4o (dict-based criteria)")
result_dict = eval_dict.run(summarizer, samples_per_datapoint=1, n_workers=4, verbose=True)
print(result_dict.scores)
print("Mean critic score:", np.mean([s['score'] for s in result_dict.scores]))
print("Mean length of completions:", np.mean([s['length'] for s in result_dict.scores]))