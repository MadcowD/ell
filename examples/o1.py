import ell

@ell.simple(model="o1-preview")
def solve_complex_math_problem(equation: str, variables: dict, constraints: list, optimization_goal: str):
    return f"""You are an expert mathematician and problem solver. Please solve the following complex mathematical problem:

Equation: {equation}
Variables: {variables}
Constraints: {constraints}
Optimization Goal: {optimization_goal}"""

@ell.simple(model="o1-preview")
def write_plot_code_for_problem_and_solution(solution :str):
    return f"""You are an expert programmer and problem solver. 
Please write code in python with matplotlib to plot the solution to the following problem: It should work in the terminal. Full script with imports.
IMPORTANT: Do not include any other text only the code.
Solution to plot: {solution}"""

def solve_and_plot(**kwargs):
    solution = solve_complex_math_problem(**kwargs)
    plot_code = write_plot_code_for_problem_and_solution(solution)
    # remove backticks and ```python
    plot_code = plot_code.replace("```python", "").replace("```", "").strip()
    exec(plot_code)
    return solution

if __name__ == "__main__":

    ell.init(store='./logdir', autocommit=True, verbose=True)
    result = solve_and_plot(
        equation="y = ax^2 + bx + c",
        variables={"a": 1, "b": -5, "c": 6},
        constraints=["x >= 0", "x <= 10"],
        optimization_goal="Find the minimum value of y within the given constraints"
    )
    print(result)