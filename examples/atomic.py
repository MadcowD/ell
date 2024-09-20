# Install Groq and ell if not already installed
# pip install groq ell

import logging
import ell
from ell.models.groq import get_groq_client
from typing import List, Dict, Any
import json
import time  # Import the time module to introduce delays

# Constants
MAX_RETRIES = 3
MINIMUM_SIZE_THRESHOLD = 50  # Define based on context
DELAY_BETWEEN_CALLS = 3  # Delay in seconds between ell calls

# Configure logging to display INFO and above messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_response(response: str) -> List[str]:
    """
    Parse the response from the language model into a list of subproblems or steps.
    Attempts to parse as JSON; falls back to newline-separated list.
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return [line.strip() for line in response.split('\n') if line.strip()]

@ell.simple(model="llama-3.1-8b-instant")
def DecomposeToAtomic(problem: str) -> str:
    """
    Decompose the main problem into atomic subproblems using Groq.
    """
    prompt = (
        "You are a highly skilled problem solver. "
        f"Decompose the following problem into atomic subproblems: {problem}"
    )
    return prompt

@ell.simple(model="gemma2-9b-it")
def SolveAtomicSubproblem(subproblem: str) -> str:
    """
    Solve an atomic subproblem using Groq.
    """
    prompt = (
        "You are solving an atomic subproblem. "
        f"Solve the following atomic subproblem: {subproblem}"
    )
    return prompt

@ell.simple(model="llama-3.1-8b-instant")
def VerifyStepResult(subproblem: str, result: str) -> str:
    """
    Verify whether the result of a subproblem matches the expected outcome using Groq.
    """
    prompt = (
        "You are verifying the result of a step. "
        f"Does the result '{result}' satisfy the requirements of the subproblem '{subproblem}'? "
        "Respond with 'True' or 'False'."
    )
    return prompt

@ell.simple(model="gemma2-9b-it")
def DefineSteps(subproblem: str) -> str:
    """
    Define the steps required to solve an atomic subproblem using Groq.
    """
    prompt = (
        "You are defining the steps required to solve an atomic subproblem. "
        f"Define the steps for solving the subproblem: {subproblem}"
    )
    return prompt

class ProblemTree:
    """
    Manages the hierarchical structure and status of the problem and its subproblems.
    """
    def __init__(self, root: str):
        self.root = root
        self.nodes: Dict[str, Dict[str, Any]] = {root: {'status': 'Unsolved', 'children': []}}
        logger.info(f"Initialized ProblemTree with root: '{root}'")
    
    def update_node(self, problem: str, status: str):
        """
        Update the status of a node in the problem tree.
        """
        if problem in self.nodes:
            self.nodes[problem]['status'] = status
        else:
            self.nodes[problem] = {'status': status, 'children': []}
        logger.info(f"Updated '{problem}' status to '{status}'.")
    
    def add_children(self, parent_problem: str, subproblems: List[str]):
        """
        Add subproblems as children of the parent problem in the tree.
        """
        if parent_problem in self.nodes:
            self.nodes[parent_problem]['children'].extend(subproblems)
        else:
            self.nodes[parent_problem] = {'status': 'Unsolved', 'children': subproblems}
        for subproblem in subproblems:
            self.nodes[subproblem] = {'status': 'Unsolved', 'children': []}
        logger.info(f"Added children to '{parent_problem}': {subproblems}")

def HandleError(subproblem: str, step: str, result: str, problem_tree: 'ProblemTree', retry_tracker: Dict[str, int]):
    """
    Handle errors by logging them and retrying the step if possible.
    """
    # Log the error
    logger.error(f"Error in subproblem '{subproblem}', step '{step}': Expected result not achieved. Got '{result}'")
    
    # Get current retry count
    current_retry = retry_tracker.get(step, 0)
    
    if current_retry < MAX_RETRIES:
        retry_tracker[step] = current_retry + 1
        logger.info(f"Retrying step '{step}' ({retry_tracker[step]}/{MAX_RETRIES})")
        
        # Execute the step again
        new_result_response = ExecuteStep(step)
        time.sleep(DELAY_BETWEEN_CALLS)  # Delay after executing the step
        new_result = new_result_response.strip()
        logger.info(f"Retried step '{step}' with result: {new_result}")
        
        # Verify the new result
        verification_response = VerifyStepResult(subproblem, new_result)
        is_valid = verification_response.strip().lower() == 'true'
        logger.info(f"Verification for retried step '{step}' returned: {is_valid}")
        
        if is_valid:
            problem_tree.update_node(step, 'Solved')
        else:
            HandleError(subproblem, step, new_result, problem_tree, retry_tracker)
    else:
        problem_tree.update_node(subproblem, 'Failed')
        logger.error(f"Subproblem '{subproblem}' failed after {MAX_RETRIES} retries.")
        raise Exception(f"Subproblem '{subproblem}' failed after {MAX_RETRIES} retries.")

def ExecuteStep(step: str) -> str:
    """
    Execute a step by solving the atomic subproblem.
    """
    result = SolveAtomicSubproblem(step)
    time.sleep(DELAY_BETWEEN_CALLS)  # Delay after solving the step
    return result

def IsAtomic(subproblem: str) -> bool:
    """
    Determine if a subproblem is atomic based on its size.
    """
    is_atomic = len(subproblem) <= MINIMUM_SIZE_THRESHOLD
    logger.info(f"Subproblem '{subproblem}' is {'atomic' if is_atomic else 'not atomic'}.")
    return is_atomic

def CreateAtomicProblemTree(root_problem: str, subproblems: List[str]) -> ProblemTree:
    """
    Initialize the problem tree with the root problem and its atomic subproblems.
    """
    problem_tree = ProblemTree(root=root_problem)
    problem_tree.add_children(root_problem, subproblems)
    return problem_tree

def AddSubproblemsToTree(problem_tree: ProblemTree, parent_subproblem: str, subproblems: List[str]):
    """
    Add newly decomposed subproblems to the problem tree under the parent subproblem.
    """
    problem_tree.add_children(parent_subproblem, subproblems)

def DecomposeToAtomicRecursive(subproblem: str, problem_tree: ProblemTree, retry_tracker: Dict[str, int]):
    """
    Recursively decompose a subproblem until all are atomic and add them to the problem tree.
    """
    if IsAtomic(subproblem):
        return
    # Decompose the subproblem
    smaller_subproblems_response = DecomposeToAtomic(subproblem)
    time.sleep(DELAY_BETWEEN_CALLS)  # Delay after decomposing the subproblem
    smaller_subproblems = parse_response(smaller_subproblems_response)
    AddSubproblemsToTree(problem_tree, subproblem, smaller_subproblems)
    for smaller_subproblem in smaller_subproblems:
        DecomposeToAtomicRecursive(smaller_subproblem, problem_tree, retry_tracker)
        SolveAtomicSubproblemRecursive(smaller_subproblem, problem_tree, retry_tracker)

def SolveAtomicSubproblemRecursive(subproblem: str, problem_tree: ProblemTree, retry_tracker: Dict[str, int]):
    """
    Recursively solve an atomic subproblem, handling decomposition if necessary.
    """
    if IsAtomic(subproblem):
        # Define steps for the atomic subproblem
        steps_response = DefineSteps(subproblem)
        time.sleep(DELAY_BETWEEN_CALLS)  # Delay after defining steps
        steps = parse_response(steps_response)
        logger.info(f"Defined steps for subproblem '{subproblem}': {steps}")
        for step in steps:
            try:
                # Execute the step
                result_response = ExecuteStep(step)
                # The delay is already handled in ExecuteStep
                result = result_response.strip()
                logger.info(f"Solved step '{step}' with result: {result}")
                
                # Verify the step result
                verification_response = VerifyStepResult(subproblem, result)
                time.sleep(DELAY_BETWEEN_CALLS)  # Delay after verification
                is_valid = verification_response.strip().lower() == 'true'
                logger.info(f"Verification for step '{step}' returned: {is_valid}")
                
                if is_valid:
                    problem_tree.update_node(step, 'Solved')
                else:
                    HandleError(subproblem, step, result, problem_tree, retry_tracker)
            except Exception as e:
                logger.error(f"Exception occurred while solving step '{step}': {e}")
                problem_tree.update_node(step, 'Failed')
    else:
        # Decompose the subproblem further
        smaller_subproblems_response = DecomposeToAtomic(subproblem)
        time.sleep(DELAY_BETWEEN_CALLS)  # Delay after decomposing
        smaller_subproblems = parse_response(smaller_subproblems_response)
        AddSubproblemsToTree(problem_tree, subproblem, smaller_subproblems)
        for smaller_subproblem in smaller_subproblems:
            DecomposeToAtomicRecursive(smaller_subproblem, problem_tree, retry_tracker)
            SolveAtomicSubproblemRecursive(smaller_subproblem, problem_tree, retry_tracker)

def SolveProblem(problem: str) -> ProblemTree:
    """
    Orchestrate the entire problem-solving process.
    """
    logger.info(f"Starting to solve problem: '{problem}'")
    
    # Decompose the problem into atomic subproblems
    subproblems_response = DecomposeToAtomic(problem)
    time.sleep(DELAY_BETWEEN_CALLS)  # Delay after decomposing the main problem
    subproblems = parse_response(subproblems_response)
    
    # Create a detailed problem tree to manage subproblems
    problem_tree = CreateAtomicProblemTree(root_problem=problem, subproblems=subproblems)
    
    # Initialize retry tracker
    retry_tracker = {}
    
    # Execute and verify each atomic subproblem
    for subproblem in subproblems:
        SolveAtomicSubproblemRecursive(subproblem, problem_tree, retry_tracker)
    
    logger.info(f"Final Problem Tree: {json.dumps(problem_tree.nodes, indent=2)}")
    return problem_tree

def main():
    """
    Main function to initialize Groq client and execute the problem-solving workflow.
    """
    try:
        # Obtain Groq client
        client = get_groq_client()
        logger.info(f"Successfully obtained Groq client: {type(client).__name__}")
        
        # Initialize ell with verbose logging if needed
        ell.init(store='./logdir', verbose=True)
        
        # Example usage
        problem = "How mant r are in the word Strawberry"
        problem_tree = SolveProblem(problem)
        
        # Optionally, print the final problem tree
        print("Final Problem Tree:")
        print(json.dumps(problem_tree.nodes, indent=2))
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
        main()
