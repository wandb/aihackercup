import os
import weave
import asyncio
import logging
from pathlib import Path
from pydantic import BaseModel, Field

WEAVE_PROJECT = "ai-hacker-cup"
weave_client = weave.init(WEAVE_PROJECT)

os.environ["STRONG_LLM"] = "o1-preview"
os.environ["FAST_LLM"] = "gpt-4o"
os.environ["API_KEY"] = os.environ["OPENAI_API_KEY"]
os.environ["MAX_TOKENS"] = "8000"
os.environ["WEAVE_PARALLELISM"] = "5"


# Start of workout
from utils import async_client, STRONG_LLM, format_response, check_correctness, find_problems

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# get current dataset!
ds2024 = Path("./2024/practice")
problems = find_problems(ds2024)

class Solution(BaseModel):
    core_question: str = Field(..., description="Core question of the problem")
    problem_solving_info: str = Field(..., description="Problem-solving information related to the core question")
    plan: str = Field(..., description="Step by step plan to solve the problem")
    pseudocode: str = Field(..., description="Pseudocode to solve the problem")
    source_code: str = Field(..., description="Valid Python3 sourcecode to solve the problem.")



system_prompt = """
You are a world-class competitive programmer tasked with solving a programming problem. 
You will be provided with a problem statement, and you need to create a Python3 solution for it. 
Your task it to develop a winning solution to the problem in Python3 programming language.
You will do this in a step-by-step manner.

Step 1: Extract the core question and the problem-solving information from the problem statement.
Step 2: Generate a step by step plan to solve the problem.
Step 3: Generate the pseudocode to solve the problem.
Step 4: Write the final solution in Python3 programming language to solve the problem.

Competition Guidelines:
    a. Do not use any external libraries; stick to Python 3 standard library
    b. Handle input and output using standard input/output (stdin/stdout)
    c. Use helper functions to improve readability of the code.
    c. Use the `input()` function to take input from stdin and print the output to stdout.
    d. Do not add extra print statements otherwise it will fail the test cases.
    e. Make sure your code passes all potential test cases, including edge cases
    f. Follow the input/output format specified in the problem statement and the sample test cases."""

prompt_template = """
Let's think step by step to solve the problem:

Problem: 
{problem_description}

Input: 
{sample_input}

Output: 
{sample_output}
"""

@weave.op
async def one_shot_solver(
    problem: Problem, 
    system_prompt: str, 
    prompt_template: str,
    temperature: float = 0.7,
    timeout: int = 10
) -> str:
    logging.info(f"Solving problem: {problem.problem_name}")

    @weave.op
    def format_prompt(system_prompt: str, prompt_template: str, problem: Problem) -> str:
        return system_prompt + prompt_template.format(
            problem_description=problem.problem_description,
            sample_input=problem.sample_input,
            sample_output=problem.sample_output
        )

    # call model one first time to get the code
    logging.info("Calling model to solve the problem")
    model_output = await async_client.chat.completions.create(
        model=STRONG_LLM,
        messages=[
            {"role": "user", "content": format_prompt(system_prompt, prompt_template, problem)}
        ],
        response_model=None
    )

    out = model_output.choices[0].message.content

    # extract code from the response
    logging.info("Formatting the response")
    solution = await format_response(out, Solution)

    # check if the code is correct
    logging.info("Checking if the code is correct")
    test_report = await check_correctness(
        solution.source_code,
        problem.sample_input,
        problem.sample_output,
        timeout=timeout,
    )

    return {"solution": solution, "test_report": test_report}


class OneShotSolver(weave.Model):
    code_execution_timeout: int = 30
    llm_model: str = STRONG_LLM
    system_prompt: str = system_prompt
    prompt_template: str = prompt_template
    temperature: float = 0.7

    @weave.op
    async def predict(self, problem: dict):
        return await one_shot_solver(
            problem=Problem(**problem), 
            system_prompt=self.system_prompt, 
            prompt_template=self.prompt_template, 
            timeout=self.code_execution_timeout,
            temperature=self.temperature
        )
    
model = OneShotSolver()


evals_dataset = [{"problem": problem.model_dump(), "expected_result": "passed"} for problem in problems]

@weave.op
def scorer(expected_result: str, model_output: dict) -> dict:
    if model_output is None or model_output["test_report"] is None:
        return {"solution_passed": False}
    return {"solution_passed": expected_result == model_output["test_report"]}

logger.info("Creating evaluator")
evaluator = weave.Evaluation(dataset=evals_dataset, scorers=[scorer], trials=1)

logger.info(f"Evaluating model: {model}")
results = asyncio.run(evaluator.evaluate(model))
logger.info(f"Evaluation results: {results}")
