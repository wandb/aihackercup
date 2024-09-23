import asyncio
import multiprocessing
import os
import pathlib
from pathlib import Path
import queue
import re
import subprocess
import sys
import logging
import time
import traceback
from typing import Any, List
import math

import weave
import openai
import instructor

from pydantic import BaseModel, Field
from tree_sitter_languages import get_language, get_parser


# API params
BASE_URL = os.getenv("BASE_URL", None)
API_KEY = os.getenv("API_KEY", "dummy_key")

# params
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))
FAST_LLM = os.getenv("FAST_LLM", "open-mistral-nemo-2407")
STRONG_LLM = os.getenv("STRONG_LLM", "mistral-large-latest")

# API client
oai_client = openai.AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
async_client = instructor.from_openai(oai_client, mode=instructor.Mode.JSON)

language = get_language("python")
tree_parser = get_parser("python")

import re

def maybe_remove_backticks(solution: str) -> str:
    "Remove backticks from the solution"
    solution = solution.strip()
    solution = re.sub(r'^```python\s*', '', solution)
    solution = re.sub(r'\s*```$', '', solution)
    return solution


def remove_extra_newlines(text: str) -> str:
    # Use regex to replace 2 or more newlines (with possible whitespace in between) with a single newline
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text


def remove_comments_and_docstrings(code):
    # Define queries to capture comments and docstrings
    doc_str_pattern = """
    (module . (expression_statement (string)) @module_doc_str)
    (class_definition body: (block . (expression_statement (string)) @class_doc_str))
    (function_definition body: (block . (expression_statement (string)) @function_doc_str))
    """

    comment_pattern = "(comment) @comment"
    # Parse the code
    tree = tree_parser.parse(code.encode())
    root_node = tree.root_node

    # Query the tree for docstrings and comments
    doc_str_query = language.query(doc_str_pattern)
    doc_strs = doc_str_query.captures(root_node)

    comment_query = language.query(comment_pattern)
    comments = comment_query.captures(root_node)

    # Get the start and end points of all docstrings and comments
    doc_str_points = set((node.start_byte, node.end_byte) for node, _ in doc_strs)
    comment_points = set((node.start_byte, node.end_byte) for node, _ in comments)

    # Create a set of all points to remove
    remove_points = doc_str_points.union(comment_points)

    # Reconstruct the code, skipping over the parts to remove
    cleaned_code = []
    last_index = 0
    for start, end in sorted(remove_points):
        if last_index < start:
            cleaned_code.append(code[last_index:start])
        last_index = end

    # Add any remaining code after the last comment/docstring
    cleaned_code.append(code[last_index:])

    return "".join(cleaned_code)


def clean_code_string(code: str) -> str:
    code = remove_comments_and_docstrings(code)
    code = remove_extra_newlines(code)
    return code

class TestReport(BaseModel):
    status: str
    message: str

    @property
    def as_xml(self) -> str:
        return f"""
<test_report>
<status>{self.status}</status>
<message>{self.message}</message>
</test_report>
"""

def compare_lines_with_tolerance(expected: str, actual: str, tolerance: float = 1e-9) -> bool:
    """
    Compare two lines of output with a tolerance for floating point numbers.
    """
    expected_lines = expected.strip().split('\n')
    actual_lines = actual.strip().split('\n')

    if len(expected_lines) != len(actual_lines):
        return False

    for expected_line, actual_line in zip(expected_lines, actual_lines):
        expected_match = re.match(r"Case #\d+: (.+)", expected_line)
        actual_match = re.match(r"Case #\d+: (.+)", actual_line)

        if not expected_match or not actual_match:
            return False

        expected_values = expected_match.group(1).split()
        actual_values = actual_match.group(1).split()

        if len(expected_values) != len(actual_values):
            return False

        for expected_value, actual_value in zip(expected_values, actual_values):
            try:
                expected_float = float(expected_value)
                actual_float = float(actual_value)
                if not math.isclose(expected_float, actual_float, rel_tol=tolerance):
                    return False
            except ValueError:
                if expected_value != actual_value:
                    return False

    return True

async def exec_program(program, input_data, expected_output, timeout):
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-c", program,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(input=input_data.encode()), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            return TestReport(
                status="timeout",
                message=f"Took too long! Your program timed out after {timeout} seconds of execution."
            )
        
        if process.returncode != 0:
            return TestReport(
                status="error", message=f"Program execution failed: {stderr.decode()}"
            )
        else:
            if compare_lines_with_tolerance(expected_output, stdout.decode()):
                return TestReport(
                    status="passed", message="Yay! Your program ran successfully"
                )
            else:
                return TestReport(
                    status="failed",
                    message=f"<expected>\n{expected_output}</expected>\n---\n<got>\n{stdout.decode()}</got>",
                )
    except Exception:
        return TestReport(
            status="error", message=f"An error occurred: {traceback.format_exc()}"
        )

@weave.op
async def check_correctness(
    program: str, input_data: str, expected_output: str, timeout: float
) -> TestReport:
    return await exec_program(program, input_data, expected_output, timeout)


@weave.op
async def format_response(text: str, model: Any, temperature: float = 0.1) -> Any:
    formatted_response = await async_client.chat.completions.create(
        model=FAST_LLM,
        # Instructor adds a system message by default about how to format the response given the response model.
        messages=[
            {
                "role": "user",
                "content": f"Extract the relevant information from the following document and return it in valid JSON\n\n{text}",
            }
        ],
        temperature=temperature,
        response_model=model,
        max_retries=2,
        max_tokens=MAX_TOKENS,
    )
    return formatted_response


class Problem(BaseModel):
    problem_dir: pathlib.Path = Field(
        ..., description="The path to the problem directory"
    )
    problem_name: str = Field(..., description="The name of the problem")
    problem_description: str = Field(..., description="The description of the problem")
    sample_input: str = Field(..., description="The sample input of the problem")
    sample_output: str = Field(..., description="The sample output of the problem")
    problem_input: pathlib.Path = Field(..., description="The path to the input file")
    problem_output: pathlib.Path = Field(..., description="The path to the output file")

    @property
    def as_xml(self) -> str:
        return f"""
<problem>
<problem_statement>
{remove_extra_newlines(self.problem_description)}
</problem_statement>
<sample_test_cases>
<sample_input>
{self.sample_input}
</sample_input>
<sample_output>
{self.sample_output}
</sample_output>
</sample_test_cases>
</problem>
"""

    @classmethod
    def from_name(cls, problem_name: str, folder_path: Path):
        description_path = folder_path / f"{problem_name}.md"
        sample_input_path = folder_path / f"{problem_name}_sample_input.txt"
        sample_output_path = folder_path / f"{problem_name}_sample_output.txt"
        input_path = folder_path / f"{problem_name}.in"
        output_path = folder_path / f"{problem_name}.out"

        return cls.from_files(
            problem_name=problem_name,
            description_path=description_path,
            sample_input_path=sample_input_path,
            sample_output_path=sample_output_path,
            input_path=input_path,
            output_path=output_path,
        )

    @classmethod
    def from_files(
        cls, 
        problem_name: str, 
        description_path: Path, 
        sample_input_path: Path, 
        sample_output_path: Path, 
        input_path: Path,
        output_path: Path = None,
    ):
        return cls(
            problem_name=problem_name,
            problem_description=description_path.read_text(),
            sample_input=sample_input_path.read_text(),
            sample_output=sample_output_path.read_text(),
            problem_input=input_path,
            problem_output=output_path if output_path else input_path.with_suffix('.out'),
            problem_dir=input_path.parent,
        )
    
def find_problems(folder: Path) -> list[dict]:
    """
    Find all the problems in the given folder.
    """
    problems = []

    # search for all files ending in .in
    problem_names = [file.stem for file in folder.glob("**/*.in")]
    for problem_name in problem_names:
        try:
            problems.append(Problem.from_name(problem_name, folder))
        except Exception as e:
            logging.error(f"Error loading problem {problem_name}: {e}")
    logging.info(f"Found {len(problems)} problems")
    return problems

class Analysis(BaseModel):
    core_question: str = Field(..., description="Core question of the problem")
    problem_solving_info: List[str] = Field(
        ..., description="Problem-solving information related to the core question"
    )
    algorithm: str = Field(..., description="Algorithm to solve the problem")
    tutorial: str = Field(..., description="Tutorial on the algorithm")
    plan: str = Field(..., description="Step by step plan to solve the problem")
    pseudocode: str = Field(..., description="Pseudocode to solve the problem")

    @property
    def as_xml(self) -> str:
        return f"""
<core_question>
{self.core_question}
</core_question>
<problem_solving_info>
{self.problem_solving_info}
</problem_solving_info>
<algorithm>
{self.algorithm}
</algorithm>
<tutorial>
{self.tutorial}
</tutorial>
<plan>
{self.plan}
</plan>
<pseudocode>
{self.pseudocode}
</pseudocode>
"""


class Solution(Analysis):
    source_code: str = Field(
        ..., description="Valid Python3 sourcecode to solve the problem."
    )

    @property
    def as_xml(self) -> str:
        return f"""
<root>
{super().as_xml}
<source_code>
{self.source_code}
</source_code>
</root>
"""


class Reflection(BaseModel):
    reflection: str = Field(
        ...,
        description="Reflection on the problem, your solution, and the correct answer.",
    )
    keywords: List[str] = Field(
        ...,
        description="Keywords that describe the type of your errors from most general to most specific.",
    )
    step_by_step_solution: str = Field(
        ...,
        description="Step by step solution to the problem based on your knowledge of the correct answer.",
    )
    instructions: List[str] = Field(
        ...,
        description="Detailed instructions to help you correctly solve this problem in the future.",
    )
    general_advice: List[str] = Field(
        ...,
        description="General advice to help you solve similar types of problems in the future.",
    )

    @property
    def as_xml(self) -> str:
        return f"""
<root>
<reflection>
{self.reflection}
</reflection>
<keywords>
{self.keywords}
</keywords>
<step_by_step_solution>
{self.step_by_step_solution}
</step_by_step_solution>
<instructions>
{self.instructions}
</instructions>
<general_advice>
{self.general_advice}
</general_advice>
</root>
"""


def format_example(example: dict) -> str:
    formatted_doc = f"""
<problem>
<problem_statement>
{example['description']}
</problem_statement>
</problem>
<solution>
{example['code']}
</solution>
"""
    return formatted_doc


def format_examples(examples: List[dict], analyses: List[Analysis]) -> str:
    def format_question(example: dict) -> str:
        return f"""
<problem>
<problem_statement>
{example['description']}
</problem_statement>
</problem>
"""

    def format_solution(analysis: Analysis, example: dict) -> str:
        return f"""
<root>
{analysis.as_xml}
<source_code>
{example['code']}
</source_code>
</root>
"""

    messages = ""
    for example, analysis in zip(examples, analyses):
        messages += f"\n<example>{format_question(example)}\n{format_solution(analysis, example)}</example>\n"
    return messages.strip()
