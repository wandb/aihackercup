import os
import weave

WEAVE_PROJECT = "ai-hacker-cup"
weave_client = weave.init(WEAVE_PROJECT)


STRONG_LLM = "o1-preview"
FAST_LLM = "gpt-4o"

os.environ["FAST_LLM"] = FAST_LLM  # We'll use stong model everywhere
os.environ["STRONG_LLM"] = STRONG_LLM

os.environ["API_KEY"] = os.environ["OPENAI_API_KEY"]

os.environ["MAX_TOKENS"] = "4096"
os.environ["WEAVE_PARALLELISM"] = "5"


import asyncio
import logging
from pydantic import BaseModel, Field

# Start of workout
from utils import Problem, async_client, STRONG_LLM, format_response, check_correctness

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# get dataset
practice_dataset_uri = "weave:///parambharat/hackercup/object/practice_dataset:R35fXf9N3FE2IOesg7bRPaPAxiE9YbpirhXO9HcHs8w"
problems_dataset = weave.ref(practice_dataset_uri).get().rows[:]
problems = list(map(lambda x: Problem(**x), problems_dataset))


class Solution(BaseModel):
    solution_explanation: str = Field(..., description="Detailed explanation of the solution")
    source_code: str = Field(..., description="Valid Python3 sourcecode to solve the problem.")



prompt_template = """
You will be provided with a problem statement, and you need to create a Python3 solution for it. 
Your task it to develop a winning solution to the problem in Python3 programming language.

- Write the solution in Python3 programming language to solve the problem.

Competition Guidelines:
    a. Do not use any external libraries; stick to Python 3 standard library
    b. Handle input and output using standard input/output (stdin/stdout)
    c. Use helper functions to improve readability of the code.
    c. Use the `input()` function to take input from stdin and print the output to stdout.
    d. Do not add extra print statements otherwise it will fail the test cases.
    e. Follow the input/output format specified in the problem statement and the sample test cases.


Here is the problem statement:

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
    prompt_template: str,
    timeout: int = 10
) -> str:
    logging.info(f"Solving problem: {problem.problem_name}")

    # call model one first time to get the code
    logging.info("Calling model to solve the problem")
    model_output = await async_client.chat.completions.create(
        model=STRONG_LLM,
        messages=[
            {"role": "user", "content": prompt_template.format(
                problem_description=problem.problem_description,
                sample_input=problem.sample_input,
                sample_output=problem.sample_output)}
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
    prompt_template: str = prompt_template

    @weave.op
    async def predict(self, problem: dict):
        return await one_shot_solver(
            problem=Problem(**problem), 
            prompt_template=self.prompt_template, 
            timeout=self.code_execution_timeout,
        )
    
model = OneShotSolver()

evals_dataset = [{"problem": problem.model_dump(), "expected_result": "passed"} for problem in problems]

@weave.op
def scorer(expected_result: str, model_output: dict) -> dict:
    if model_output is None or model_output["test_report"].status is None:
        return {"solution_passed": False}
    return {"solution_passed": expected_result == model_output["test_report"].status} # check if the test_report status == passed

logger.info("Creating evaluator")
evaluator = weave.Evaluation(dataset=evals_dataset, scorers=[scorer], trials=1)

logger.info(f"Evaluating model: {model}")
results = asyncio.run(evaluator.evaluate(model))
logger.info(f"Evaluation results: {results}")
