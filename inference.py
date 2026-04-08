import os
from openai import OpenAI
from client import APIDocClient
from server.models import DocAction

client = OpenAI(
    base_url=os.environ["API_BASE_URL"],
    api_key=os.environ["HF_TOKEN"],
)

env = APIDocClient(base_url=os.environ["ENV_URL"]).sync()

try:
    for level in ["easy", "medium", "hard"]:
        with env:
            result = env.reset(level=level)
            snippet = result.observation.code_snippet

            response = client.chat.completions.create(
                model=os.environ["MODEL_NAME"],
                messages=[
                    {"role": "system", "content": "You write Python docstrings."},
                    {"role": "user", "content": f"Write documentation for:\n\n{snippet}"},
                ],
            )

            doc = response.choices[0].message.content
            result = env.step(DocAction(generated_doc=doc))
            print(f"{level}: score = {result.reward}")
            print(f"  {result.observation.feedback}")
finally:
    env.close()