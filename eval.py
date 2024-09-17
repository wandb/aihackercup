import asyncio
import os
import sys
import logging
from dataclasses import dataclass
from pathlib import Path

import weave
import simple_parsing
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

async def run_python(program: Path, input_file: Path, output_file: Path, timeout: float = 10):
    """
    Run a Python program with the given input file and output file.
    """
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, program,
            stdin=input_file.open('rb'),
            stdout=output_file.open('wb'),
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            process.kill()
            raise TimeoutError(f"Program execution timed out after {timeout} seconds")
        
        if process.returncode != 0:
            raise RuntimeError(f"Program execution failed: {stderr.decode()}")
        
        logging.info(f"Output saved to {output_file}")
    except Exception as e:
        raise RuntimeError(f"Error running Python program: {str(e)}")

async def run_cpp(cpp_file: Path, input_file: Path, output_file: Path, timeout: float = 10):
    """
    Run a C++ program with the given input file and output file.
    """
    # Get the base name of the cpp file (without extension)
    base_name = os.path.splitext(cpp_file.name)[0]
    
    # Compile the C++ program
    compile_command = f"g++ {cpp_file} -o {base_name}"
    process = await asyncio.create_subprocess_shell(
        compile_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise RuntimeError(f"Compilation failed: {stderr.decode()}")
    
    try:
        # Run the compiled program with input from file
        with open(input_file, 'r') as infile:
            process = await asyncio.create_subprocess_exec(
                f"./{base_name}",
                stdin=infile,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Program execution timed out after {timeout} seconds")
            
            if process.returncode != 0:
                raise RuntimeError(f"Program execution failed: {stderr.decode()}")
            
            output_file.write_text(stdout.decode())
        
        logging.info(f"Output saved to {output_file}")
    
    finally:
        # Clean up the compiled file
        if os.path.exists(base_name):
            os.remove(base_name)

@weave.op
async def run_program(program: Path, input: Path, output: Path, timeout: float = 10):
    if program.suffix == ".cpp":
        logging.info(f"Running C++ program: {program}")
        await run_cpp(program, input, output, timeout)
    elif program.suffix == ".py":
        logging.info(f"Running Python program: {program}")
        await run_python(program, input, output, timeout)
    else:
        raise ValueError(f"Unsupported file type: {program.suffix}")
    return "success"

@weave.op
def check_solution(model_output: str, expected_output: str):
    print(f"In Check Solution: {model_output}, {expected_output}")
    output = Path(model_output["generated_output"]).read_text() # these may be big!
    expected_output = Path(expected_output).read_text()
    return {"solved": output.strip() == expected_output.strip()}

@dataclass
class Args(simple_parsing.Serializable):
    program: str = "dataset/2023/practice/cheeseburger_corollary_ch1.cpp"
    input: str = "dataset/2023/practice/cheeseburger_corollary_ch1.in"
    output: str = "dataset/2023/practice/cheeseburger_corollary_ch1.out"
    eval_name: str = "super_dupper_model"
    weave_project: str = "hackercup-eval-solution"
    timeout: float = 10

if __name__=="__main__":
    args = simple_parsing.parse(Args)
    weave.init(args.weave_project)
    
    generated_output_file = Path("generated_output.txt")

    asyncio.run(run_program(
        Path(args.program),
        Path(args.input),
        generated_output_file,
        timeout=args.timeout
    ))

    passed = check_solution({"generated_output": generated_output_file}, Path(args.output))
    logging.info(f"Program passed: {passed}")

    class Runner(weave.Model):
        timeout: float = 10

        @weave.op
        async def predict(self, program: str, input: str):
            program, input = Path(program), Path(input)
            print(program, input)
            generated_output = input.parent / (input.stem + "_generated_output.txt")
            print(f"Saving generated output to {generated_output}")
            status = await run_program(program, input, generated_output, timeout=self.timeout)
            predict_output =  {"generated_output": generated_output, "status": status}
            print(f"Predict output: {predict_output}")
            return predict_output



    dataset = [{
        "program": args.program,
        "input": args.input,
        "expected_output": args.output,
    }]


    model = Runner(timeout=args.timeout)

    # out = asyncio.run(model.predict(args.program, args.input))
    
    # passed = check_solution(out["model_output"], args.output)
    # logging.info(f"Program passed: {passed}")
    print("="*100)
    # run the eval
    evaluation = weave.Evaluation(dataset=dataset, scorers=[check_solution])
    asyncio.run(evaluation.evaluate(model))