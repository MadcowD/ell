import ell
from ell.evaluation.evaluation import Evaluation

ell.init(verbose=True, store='./logdir')


@ell.simple(model="gpt-4o", temperature=0.7)
def math_problem_solver(problem: str):
    """You are an extremely smart math problem solver. You are given a math problem and you need to solve it. Output your answer in the following format 
    'Let's think step by step: <at least 10 steps of reasoning and calculations>
    
    Answer:\\n{Answer}'

    Never incldue any other text except for Answer: new line ...    
"""
    return problem



import random

# Set fixed random seed for reproducibility
random.seed(42)

def generate_arithmetic_dataset(num_examples=100):
    operations = ['+', '-', '*', '/']
    dataset = []
    
    for _ in range(num_examples):
        # Generate random numbers up to 5 digits
        num1 = random.randint(0, 99999)
        num2 = random.randint(1, 99999) # Avoid 0 for division
        op = random.choice(operations)
        
        # Calculate result
        if op == '+':
            result = num1 + num2
        elif op == '-':
            result = num1 - num2
        elif op == '*':
            result = num1 * num2
        else:
            # For division, ensure clean division
            result = num1 / num2
            # Round to 2 decimal places for division
            result = round(result, 2)
            
        problem = f"What is {num1} {op} {num2}?"
        dataset.append({
            "input": [problem],
            "output": f"Answer:\\n{result}"
        })
    
    return dataset


def answer_is_close_l2(datapoint, result):
    try:
        result_val = float(result.split("Answer:")[1].strip().replace("\\n", ""))
        expected_val = float(datapoint["output"].split("Answer:")[1].strip().replace("\\n", ""))
        return -abs(result_val - expected_val)
    except:
        return float(-10)  # Return worst possible score if parsing fails

arithmetic_eval = Evaluation(
    name="Arithmetic",
    dataset=generate_arithmetic_dataset(),
    metrics={"answer_is_close_l2": answer_is_close_l2},
    criterion=lambda datapoint, result: result.split("Answer:")[1].strip() in datapoint["output"],
)


if __name__ == "__main__":
    arithmetic_eval.run(math_problem_solver, n_workers=20)
    print(math_problem_solver("What is 2 + 2?"))