# API Documentation Generator — OpenEnv Environment

An RL environment where an AI agent reads Python code and must write
accurate, structured documentation. Built for the Meta PyTorch × Scaler OpenEnv Hackathon.

## What It Does

The agent receives a Python code snippet and writes documentation for it.
A grader scores the output from 0.0 to 1.0 based on:
- **Length** (40%) — is it detailed enough?
- **Keyword coverage** (40%) — does it mention key concepts?
- **Structure** (20%) — does it use Args/Returns/Raises sections?

## Task Levels

| Level  | Task                          | Min score needed |
|--------|-------------------------------|-----------------|
| Easy   | Simple two-parameter function | 0.0 – 1.0       |
| Medium | Class with deposit/withdraw   | 0.0 – 1.0       |
| Hard   | Async retry decorator         | 0.0 – 1.0       |

## Action Space

```python
DocAction(
    documentation: str  # The docstring the agent wrote
)
```

## Observation Space

```python
DocObservation(
    code_snippet: str   # Python code to document
    task_level: str     # "easy", "medium", or "hard"
    hint: str           # What to focus on
    feedback: str       # After grading: score breakdown
    done: bool
    reward: float       # 0.0 to 1.0
)
```

## Quick Start

```python
from api_doc_env import DocEnv, DocAction

with DocEnv(base_url="https://YOUR_USERNAME-api-doc-env.hf.space").sync() as env:
    result = env.reset()
    print(result.observation.code_snippet)

    result = env.step(DocAction(documentation="Your docs here..."))
    print(f"Score: {result.reward}")
```

## Running the Inference Script

```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_token_here"
export ENV_URL="https://YOUR_USERNAME-api-doc-env.hf.space"

python inference.py
```

## Local Development

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

## Team

Starw Hats — OpenEnv Hackathon 2025