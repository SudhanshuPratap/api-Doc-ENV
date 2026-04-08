import os
from openai import OpenAI
from client import DocEnv
from models import DocAction

client = OpenAI(
    base_url=os.environ["API_BASE_URL"],
    api_key=os.environ["HF_TOKEN"],
)

env = DocEnv(base_url=os.environ["ENV_URL"])

try:
    for task_level in ["easy", "medium", "hard"]:
        result = env.reset()

        response = client.chat.completions.create(
            model=os.environ["MODEL_NAME"],
            messages=[
                {"role": "system", "content": "You write Python docstrings."},
                {"role": "user", "content": f"Write documentation for:\n\n{result.observation.code_snippet}"}
            ]
        )

        docs = response.choices[0].message.content
        result = env.step(DocAction(documentation=docs))
        print(f"{task_level}: score = {result.reward}")
finally:
    env.close()