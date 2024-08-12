from typing import Any, List
import ell
import requests
import inspect

ell.config.verbose = True


def calculator_tool(expression_to_eval : str) -> Any:
    import math
    return eval(expression_to_eval)

def get_html_of_url(url: str) -> str:
    return requests.get(url).text


AVAILABLE_TOOLS = [
    calculator_tool,
    get_html_of_url
]

@ell.lm(model="gpt-4o", temperature=0.1)
def tool_user(task: str) -> List[Any]:
    return [
        ell.system(
            f"""You are an extremely capable assistant. You have access to the following tools. To use these tools just 'call' them using python syntax and the output will be provided to the user. If a calculation can be done with a tool sue the tool do not answer the uestion. The result of the tool sue will be returned to the user. When responding only respond with the pythoin copde for calling the tool.

. Do not format in markdown. You are directly outputting python code. You can also do multiline code if you need ot import any dependency. 
{

'\n\n'.join(f"\n{inspect.getsource(tool)}" for tool in AVAILABLE_TOOLS)
}"""
        ),
        ell.user(
            "You are given the following task: " + task
        )
    ]


if __name__ == "__main__":
    print(eval(tool_user("What is the square root of pi.")))