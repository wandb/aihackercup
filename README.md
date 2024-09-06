This folder contains the implementation of a RAG agent to solve the Hacker Cup problems using LLMs.
It includes scripts for downloading and preprocessing the datasets and generating solutions using a Retrieval Model.

The RAG agent is based on a combination of a retriever and a generator model.
The retriever is used to retrieve similar historical problems and solutions from
the [codecontests](https://huggingface.co/datasets/deepmind/code_contests) dataset and prompt an LLM with few-shot
examples to generate solutions for the current problem.

You can learn more about the approach in this youtube video:

<a target="_blank" href="https://www.youtube.com/watch?v=cObBj2UpWK8">
<img src="https://img.youtube.com/vi/cObBj2UpWK8/0.jpg" width="600" height="450">
</a>

## Contents

1. `demo.ipynb`: this notebook contains a full walkthrough of the RAG agent and how to use it to solve Hacker Cup
   problems.
2. `retriever.py`: this script contains the implementation of the retriever we used.
3. `agent.py`: this script contains the implementation of three different agents we used to solve the problems.
4. `utils.py`: utility functions used in retrieving and generating solutions.
5. `requirements.txt`: list of required packages to run the code.


## W&B Lightning Competition 

### Deadline

The deadline to submit winning solutions is Friday 13th, 8am PT / 5pm CET.

### Submissions

To submit code for verification you neeed to submit the following to the [Submissions Form](ADD SUBMISSIONS FORM LINK):

- a zipped directory with a README and a requirements.txt
- a link to the [W&B Weave](https://weave-docs.wandb.ai/tutorial-eval?utm_source=colab&utm_medium=code&utm_campaign=lightning-ai-hacker-cup) evaluation


### Rules

*Note these are the rules for the W&B Lightning Competition, not the official NeurIPS AI Hacker Cup challenge*

**Generalizability**

The goal of this Lightning competition is to create solutions that are generalizable to this entire class of coding-based problem solving. As the solutions to the competition problems are available online, no code or specific references or descriptions of the solutions to these  practice questions are permitted in the prompts or datasets used. W&B decisions are final.

**Open Source**

All winning submissions code can and will be open sourced by W&B to be eligible for a prize. Winning solutions will be open sourced immediately after verification, eg if someone is the first to get to 4 out of 5 solutions correct and W&B verify and award a prize, we’ll open source that code as soon as we can, which can be during the comeptition, so that others can build on top of it to get to 5 out of 5. 

**Reproducibility**

Solutions must be reproducible, runnable code must be submitted and verified by W&B team. 

**Weave Evaluations**

Evaluations must be run using [W&B Weave](https://weave-docs.wandb.ai/tutorial-eval?utm_source=colab&utm_medium=code&utm_campaign=lightning-ai-hacker-cup) and a link to those evaluations included in the submission.

**No fine-tuning**

This quick competition isn't focussed on fine-tuning models, only the vanilla MistralAI models available via the MistralAI api can be used. You can use the local versions of these models.

**Time Limit**

There will be a 30minute time limit to generate solutions for all 5 problems, the MistraAI api will be used when running the submitted code.

**One prize per individual**

An individual can only win 1 single prize. i.e. if you are the first to solve 4 out of 5 challenges you are not eligible to win a second pair of Ray-Bans. Working in teams are allowed but there is only 1 pair of Ray-Ban per prize category, i.e. you'll have to figure out how to divide 1 pair of sunglasses among 2+ people.


