<p align="center">
  <img src="https://raw.githubusercontent.com/wandb/wandb/main/assets/logo-dark.svg#gh-dark-mode-only" width="600" alt="Weights & Biases" />
  <img src="https://raw.githubusercontent.com/wandb/wandb/main/assets/logo-light.svg#gh-light-mode-only" width="600" alt="Weights & Biases" />
</p>

# ⚡️ Competition - AI Hacker Cup


[Weights & Biases](https://wandb.ai/site?utm_source=github&utm_medium=code&utm_campaign=lightning-ai-hacker-cup) are running a 7-day Lightning Competition focussed on using LLMs to solve the 2023 practice problems for the [2024 NeurIPS AI Hacker Cup](https://hackercupai.github.io/) challenge. The competition involves solving very challenging logic problems using code.

#### Goal
The goal is to try and solve all 5 of the 2023 practice questions for the AI Hacker Cup using MistralAI's models. We’re offering free MistralAI api access via the code in this colab to get people started. For context, the **[starter notebook](https://github.com/wandb/aihackercup/blob/main/rag_code_agent.ipynb)** included in this repo has free MistralAI api access and can consistently get 2 out of 5 solutions correct using `mistral-large-latest`.

### Deadline

The deadline to submit winning solutions is Monday October 16th , 8am PT / 5pm CET.

### Prizes 

Weights & Biases are giving away a pair of Meta Ray-Ban Smart Glasses for the first individual to submit code that solves:
- 3 out of 5 correct solutions
- 4 out of 5 correct solutions
- 5 out of 5 correct solutions

(i.e. in total 3 pairs of sunglasses to give away)

## Getting Started

**Starter Notebook**

We have included a **[starter notebook](https://github.com/wandb/aihackercup/blob/main/rag_code_agent.ipynb)** which includes free MistralAI api access and which can consistently solve 2 out of 5 problems. This **[AI Hacker Cup lecture video](https://www.youtube.com/watch?v=cObBj2UpWK8)** includes an explanation of the approach taken, see the Resources section

**Discord**

The official 2024 NeurIPS Hacker Cup AI [discord is here](https://discord.gg/NkDxUd43Wf) and has a channel called `#lighting-comp-practice-problems` for discussion about this particular 7-day competition.

## Submissions

To submit code for verification you neeed to submit the following to the **[Submissions Form](https://forms.gle/5t3SgaxR11FhGAGX6)**:

- a zipped directory with a README and a requirements.txt
- a link to the [W&B Weave](https://weave-docs.wandb.ai/tutorial-eval?utm_source=github&utm_medium=code&utm_campaign=lightning-ai-hacker-cup) evaluation

You can use your own code to generate solutions or you can modify the code in this repo. The one requirement is that evaluations must be run using W&B Weave as we'll be using those logs to help verify winning solutions.

## Rules

*Note these are the rules for the W&B Lightning Competition, not the official NeurIPS AI Hacker Cup challenge*

**Generalizability**

The goal of this Lightning competition is to create solutions that are generalizable to this entire class of coding-based problem solving. As the solutions to the competition problems are available online, no code or specific references or descriptions of the solutions to these  practice questions are permitted in the prompts or datasets used. W&B decisions are final.

**Open Source**

All winning submissions code can and will be open sourced by W&B to be eligible for a prize. Winning solutions will be open sourced immediately after verification, eg if someone is the first to get to 4 out of 5 solutions correct and W&B verify and award a prize, we’ll open source that code as soon as we can, which can be during the comeptition, so that others can build on top of it to get to 5 out of 5. 

**Reproducibility**

Solutions must be reproducible, runnable code must be submitted and verified by W&B team. Given the non-deterministic nature of LLM outputs, solutions must cross the prize winning threshold in at least 2 out of 3 trials. i.e. if you submit for first to 3 out of 5 solved, your codebase must hit this performance twice out of three possible attempts.

**Weave Evaluations**

Evaluations must be run using [W&B Weave](https://weave-docs.wandb.ai/tutorial-eval?utm_source=colab&utm_medium=code&utm_campaign=lightning-ai-hacker-cup) and a link to those evaluations included in the submission.

**No fine-tuning**

This quick competition isn't focussed on fine-tuning models, only the vanilla MistralAI models available via the MistralAI api can be used. You can use the local versions of these models.

**Time Limit**

There will be a 20 minute time limit to generate solutions for all 5 problems, the MistraAI api will be used when running the submitted code.

**One prize per individual**

An individual can only win 1 single prize. i.e. if you are the first to solve 4 out of 5 challenges you are not eligible to win a second pair of Ray-Bans. Working in teams are allowed but there is only 1 pair of Ray-Ban per prize category, i.e. you'll have to figure out how to divide 1 pair of sunglasses among 2+ people.

## Resources

This folder contains the implementation of a RAG agent to solve the Hacker Cup problems using LLMs. It includes a colab and code for downloading and preprocessing the datasets and generating solutions using a Retrieval Model.

The RAG agent is based on a combination of a retriever and a generator model.
The retriever is used to retrieve similar historical problems and solutions from
the [codecontests](https://huggingface.co/datasets/deepmind/code_contests) dataset and prompt an LLM with few-shot
examples to generate solutions for the current problem.

You can learn more about the approach in this youtube video:

<a target="_blank" href="https://www.youtube.com/watch?v=cObBj2UpWK8">
<img src="https://img.youtube.com/vi/cObBj2UpWK8/0.jpg" width="600" height="450">
</a>

## Contents

1. `rag_code_agent.ipynb`: this notebook contains a full walkthrough of the RAG agent and how to use it to solve Hacker Cup
   problems.
2. `retriever.py`: this script contains the implementation of the retriever we used.
3. `agent.py`: this script contains the implementation of the agent we used to solve the problems.
4. `utils.py`: utility functions used in retrieving and generating solutions.
5. `requirements.txt`: list of required packages to run the code.



## Download Full Raw Dataset

Alternatively, you can download the dataset by running the download script from the [submit-first-solution](https://github.com/HackerCupAI/starter-kits/tree/main/submit_first_solution). Specifically, you can run the following command to download the dataset:

```bash
python download.py --year 2023 --dataset_folder data
```


This should create a `dataset` folder with the problems and solutions. Here's an example of what the data looks like for the `dim_sum_delivery` problem from the `2023` season:

```
data/dataset/2023/practice
...
├── dim_sum_delivery.cpp
├── dim_sum_delivery.in
├── dim_sum_delivery.md
├── dim_sum_delivery.out
├── dim_sum_delivery_sample_input.txt
├── dim_sum_delivery_sample_output.txt
├── dim_sum_delivery_sol.md
...
```

Each problem has a `in`, `out`, `md`, `cpp`, and `sol` file.

The `in` file contains the input data for the problem.
The `out` file contains the expected output for the problem.
The `md` file contains the problem statement.
The `cpp` file contains the source code to the solution.
The `sol` file contains the detailed solution to the problem.
The `sample_input.txt` and `sample_output.txt` files contain the sample input and output for the problem. These are the test cases that will be available to the agent during development and evaluation.
