import os
import weave
import asyncio
import logging
from pydantic import BaseModel, Field
from llama_index.core.workflow import (
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Event,
    Context,
)

# Select MistralAI models used depending if you want a fast or strong LLM
# You can see the full range of MistralAI models here: https://docs.mistral.ai/getting-started/models/
FAST_LLM = "open-mistral-nemo-2407"
STRONG_LLM = "mistral-large-latest"

os.environ["FAST_LLM"] = STRONG_LLM  # We'll use stong model everywhere
os.environ["STRONG_LLM"] = STRONG_LLM

# URL for the MistralAI api we'll be using
os.environ["BASE_URL"] = "http://195.242.25.198:8000/v1"
os.environ["API_KEY"] = "dummy_key"

# Set the max tokens for the models and how many parallel requests to make in Weave Evaluations
os.environ["MAX_TOKENS"] = "4096"
os.environ["WEAVE_PARALLELISM"] = "2"

weave.init("llamaindex-workflow")

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
class SetupEvent(Event):
    problem: Problem
    test_report: str = None

class SolvedProblemEvent(Event):
    problem: Problem
    problem_solution: str

class FormattedSolutionEvent(Event):
    problem: Problem
    solution: Solution

class OneShotSolverWorkflow(Workflow):
    retries: int = 2
    temperature: float = 0.7
    code_execution_timeout: int = 30

    @step
    @weave.op
    async def setup(self, ctx: Context, ev: StartEvent) -> SetupEvent:
        problem = ev.problem
        logging.info(f"Solving problem: {problem.problem_name}")
        messages=[
            {"role": "system", "content": ev.system_prompt},
            {"role": "user", "content": ev.prompt_template.format(
                    problem_description=problem.problem_description,
                    sample_input=problem.sample_input,
                    sample_output=problem.sample_output)}
            ]
        await ctx.set("messages", messages)
        return SetupEvent(problem=problem)
    
    @step
    @weave.op
    async def generate_code(self, ctx: Context, ev: SetupEvent) -> SolvedProblemEvent:
        messages = await ctx.get("messages")
        if ev.test_report:
            messages.append({"role": "user", "content": f"Let's try again. The previous solution was incorrect:\n {ev.test_report}"})
        logging.info("Calling model to solve the problem")
        model_output = await async_client.chat.completions.create(
            model=STRONG_LLM,
            messages=messages,
            temperature=self.temperature,
            response_model=None
        )
        problem_solution = model_output.choices[0].message.content
        messages.append({"role": "assistant", "content": problem_solution})
        await ctx.set("messages", messages)
        return SolvedProblemEvent(problem=ev.problem, problem_solution=problem_solution)

    @step
    @weave.op
    async def format_solution(self, ev: SolvedProblemEvent) -> FormattedSolutionEvent:
        logging.info("Formatting the response")
        solution = await format_response(ev.problem_solution, Solution)
        return FormattedSolutionEvent(problem=ev.problem, solution=solution)

    @step
    @weave.op
    async def check_solution(self, ev: FormattedSolutionEvent) -> StopEvent:
        logging.info("Checking if the code is correct")
        test_report = await check_correctness(
            ev.solution.source_code,
            ev.problem.sample_input,
            ev.problem.sample_output,
            timeout=self.code_execution_timeout,
        )
        logging.info(f"Test report: {test_report}")
        if (test_report.status != "passed") and self.retries > 0:
            logging.info(f"Retrying the solution. Retries left: {self.retries}")
            self.retries -= 1
            return SetupEvent(problem=ev.problem, test_report=test_report.message)
        else:
            return StopEvent(result={"solution": ev.solution, "test_report": test_report})


class OneShotSolver(weave.Model):
    code_execution_timeout: int = 30
    llm_model: str = STRONG_LLM
    system_prompt: str = system_prompt
    prompt_template: str = prompt_template
    temperature: float = 0.7

    @weave.op
    async def predict(self, problem: dict):
        workflow = OneShotSolverWorkflow(timeout=600, verbose=True)
        problem_obj = Problem(**problem)
        
        result = await workflow.run(
            problem=problem_obj,
            system_prompt=self.system_prompt,
            prompt_template=self.prompt_template,
            temperature=self.temperature,
            code_execution_timeout=self.code_execution_timeout
        )
        
        return result

model = OneShotSolver()

evals_dataset = [{"problem": problem.model_dump(), "expected_result": "passed"} for problem in problems]

# #run one example
# result = asyncio.run(model.predict(evals_dataset[0]["problem"]))
# print(result)

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
