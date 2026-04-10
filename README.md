---
title: API Doc Env
emoji: 📚
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "1.28.1"
app_file: server/app.py
pinned: false
---

# API Documentation Environment

Your app description here.
# API Documentation Generator — OpenEnv Environment

RL environment where an AI agent reads Python code and writes documentation for it.  
Built for Meta PyTorch × Scaler OpenEnv Hackathon.

## How it works

The agent gets a Python code snippet and writes a docstring. The grader scores it 0–1 based on:
- **Keyword coverage** (40%) — mentions the right concepts
- **Length** (40%) — detailed enough  
- **Structure** (20%) — has Args/Returns/Raises sections

## Task levels

| Level  | What you get                    |
|--------|---------------------------------|
| Easy   | Simple functions (`add`, `is_even`) |
| Medium | Classes with methods (`BankAccount`, `Stack`) |
| Hard   | Async decorators & context managers |

## Action & Observation

```python
# what the agent sends
DocAction(generated_doc="your docstring here")

# what the agent receives
DocObservation(
    code_snippet="def add(a, b): ...",
    task_level="easy",
    hint="Describe params and return value",
    expected_keywords=["add", "sum", "returns"],
    feedback="Score: 0.85/1.00 | ...",
    done=True,
    reward=0.85,
)
```

## Quick start

```python
from client import APIDocClient
from server.models import DocAction

with APIDocClient(base_url="https://YOUR-SPACE.hf.space").sync() as env:
    result = env.reset(level="easy")
    print(result.observation.code_snippet)

    result = env.step(DocAction(generated_doc="Your docs here..."))
    print(f"Score: {result.reward}")
```

## Running inference

```bash
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_token"
export ENV_URL="https://YOUR-SPACE.hf.space"

python inference.py
```

## Local dev

```bash
pip install -r requirements.txt
cd server
uvicorn app:app --reload
```

Then open http://localhost:8000 — the web UI is at `/web`.

## Team

Starw Hats — OpenEnv Hackathon 2025
