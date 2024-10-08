import os
import weave
import asyncio
import logging
from pathlib import Path
from pydantic import BaseModel, Field

WEAVE_PROJECT = "ai-hacker-cup"
weave_client = weave.init(WEAVE_PROJECT)

STRONG_LLM = "o1-preview"
FAST_LLM = "gpt-4o"
os.environ["FAST_LLM"] = FAST_LLM
os.environ["API_KEY"] = os.environ["OPENAI_API_KEY"]
os.environ["WEAVE_PARALLELISM"] = "5"


# Start of workout
from utils import async_client, format_response, check_correctness, find_problems, Problem, maybe_remove_backticks

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# get current dataset!
ds2024 = Path("./2024/practice")
problems = find_problems(ds2024)

class Solution(BaseModel):
    solution_explanation: str = Field(..., description="Explanation of the solution to the problem")
    source_code: str = Field(..., description="Valid Python3 sourcecode to solve the problem.")



prompt_template = """You will be provided with a problem statement, and you need to create a Python3 solution for it. 
Write the final solution in Python3 programming language to solve the problem.

## Competition Guidelines:
    a. Do not use any external libraries; stick to Python 3 standard library
    b. Handle input and output using standard input/output (stdin/stdout)
    c. Use helper functions to improve readability of the code.
    c. Use the `input()` function to take input from stdin and print the output to stdout.
    d. Do not add extra print statements otherwise it will fail the test cases.
    e. Make sure your code passes all potential test cases, including edge cases
    f. Follow the input/output format specified in the problem statement and the sample test cases.
    g. We will run the program by calling `python3 program.py` so make sure it outputs the correct results.

{problem_description}

## Sample Input: 
{sample_input}

## Expected Output: 
{sample_output}
"""

@weave.op
async def o1_solver(
    problem: Problem, 
    prompt_template: str,
    timeout: int = 10
) -> str:
    logging.info(f"Solving problem: {problem.problem_name}")

    @weave.op
    def format_prompt(prompt_template: str, problem: Problem) -> str:
        return prompt_template.format(
            problem_description=problem.problem_description,
            sample_input=problem.sample_input,
            sample_output=problem.sample_output
        )

    # call model one first time to get the code
    logging.info("Calling o1 to solve the problem")
    model_output = await async_client.chat.completions.create(
        model=STRONG_LLM,
        messages=[
            {"role": "user", "content": format_prompt(prompt_template, problem)}
        ],
        response_model=None
    )

    out = model_output.choices[0].message.content

    # extract code from the response
    logging.info("Formatting the response")
    solution = await format_response(out, Solution)
    solution.source_code = maybe_remove_backticks(solution.source_code)

    # check if the code is correct
    logging.info("Checking if the code is correct")
    test_report = await check_correctness(
        solution.source_code,
        problem.sample_input,
        problem.sample_output,
        timeout=timeout,
    )
    logging.info("Checking if the code is correct for the full problem")
    input_data = problem.problem_input.read_text()
    expected_output = problem.problem_output.read_text()
    test_report_full = await check_correctness(
        solution.source_code,
        input_data,
        expected_output,
        timeout=timeout,
    )

    return {"solution": solution, 
            "test_report": test_report,
            "test_report_full": test_report_full}


class O1ShotSolver(weave.Model):
    code_execution_timeout: int = 30
    llm_model: str = STRONG_LLM
    prompt_template: str = prompt_template

    @weave.op
    async def predict(self, problem: dict):
        return await o1_solver(
            problem=Problem(**problem), 
            prompt_template=self.prompt_template, 
            timeout=self.code_execution_timeout,
        )
    
model = O1ShotSolver()

evals_dataset = [{"problem": problem.model_dump(), "expected_result": "passed"} for problem in problems]

@weave.op
def scorer(expected_result: str, model_output: dict) -> dict:
    if model_output is None or model_output["test_report"].status is None:
        return {"solution_passed": False}
    return {"passed_sample": expected_result == model_output["test_report"].status,
            "passed_full": expected_result == model_output["test_report_full"].status}

logger.info("Creating evaluator")
evaluator = weave.Evaluation(dataset=evals_dataset, scorers=[scorer], trials=1)

logger.info(f"Evaluating model: {model}")
results = asyncio.run(evaluator.evaluate(model))
logger.info(f"Evaluation results: {results}")
