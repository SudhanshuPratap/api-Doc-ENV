import random
import re
from openenv.core.env_server import Environment
from models import DocAction, DocObservation, DocState


TASKS = {
    "easy": [
        {
            "code": "def add(a: int, b: int) -> int:\n    return a + b",
            "keywords": ["add", "sum", "parameters", "returns", "int"],
            "hint": "Describe what the function does, its parameters, and return value.",
        },
        {
            "code": "def multiply(x: float, y: float) -> float:\n    return x * y",
            "keywords": ["multiply", "product", "parameters", "returns", "float"],
            "hint": "Explain the multiplication, parameter types, and return type.",
        },
        {
            "code": "def greet(name: str) -> str:\n    return f'Hello, {name}!'",
            "keywords": ["greet", "name", "string", "returns", "hello"],
            "hint": "Describe the greeting function and its string formatting.",
        },
        {
            "code": "def is_even(n: int) -> bool:\n    return n % 2 == 0",
            "keywords": ["even", "check", "boolean", "returns", "modulo"],
            "hint": "Explain what the function checks and the return type.",
        },
    ],
    "medium": [
        {
            "code": (
                "class BankAccount:\n"
                "    def __init__(self, owner: str, balance: float = 0.0):\n"
                "        self.owner = owner\n"
                "        self.balance = balance\n\n"
                "    def deposit(self, amount: float) -> float:\n"
                "        self.balance += amount\n"
                "        return self.balance\n\n"
                "    def withdraw(self, amount: float) -> float:\n"
                "        if amount > self.balance:\n"
                "            raise ValueError('Insufficient funds')\n"
                "        self.balance -= amount\n"
                "        return self.balance"
            ),
            "keywords": ["bank", "account", "deposit", "withdraw", "balance", "owner", "raises", "ValueError"],
            "hint": "Document the class, constructor, and each method. Note the ValueError.",
        },
        {
            "code": (
                "class Stack:\n"
                "    def __init__(self):\n"
                "        self._items = []\n\n"
                "    def push(self, item) -> None:\n"
                "        self._items.append(item)\n\n"
                "    def pop(self):\n"
                "        if not self._items:\n"
                "            raise IndexError('pop from empty stack')\n"
                "        return self._items.pop()\n\n"
                "    def peek(self):\n"
                "        return self._items[-1] if self._items else None"
            ),
            "keywords": ["stack", "push", "pop", "peek", "raises", "IndexError", "LIFO"],
            "hint": "Document the data structure, all methods, and exception cases.",
        },
    ],
    "hard": [
        {
            "code": (
                "import asyncio\n"
                "from functools import wraps\n\n"
                "def retry(max_attempts: int = 3, backoff: float = 1.0):\n"
                "    def decorator(func):\n"
                "        @wraps(func)\n"
                "        async def wrapper(*args, **kwargs):\n"
                "            for attempt in range(max_attempts):\n"
                "                try:\n"
                "                    return await func(*args, **kwargs)\n"
                "                except Exception as e:\n"
                "                    if attempt == max_attempts - 1:\n"
                "                        raise\n"
                "                    await asyncio.sleep(backoff * (2 ** attempt))\n"
                "        return wrapper\n"
                "    return decorator"
            ),
            "keywords": ["retry", "async", "decorator", "backoff", "exponential", "attempts", "raises", "exception"],
            "hint": "Explain the decorator pattern, async behavior, and exponential backoff strategy.",
        },
        {
            "code": (
                "from contextlib import asynccontextmanager\n"
                "from typing import AsyncGenerator\n\n"
                "@asynccontextmanager\n"
                "async def managed_resource(name: str, timeout: float = 30.0) -> AsyncGenerator:\n"
                "    resource = await acquire(name, timeout)\n"
                "    try:\n"
                "        yield resource\n"
                "    finally:\n"
                "        await resource.release()"
            ),
            "keywords": ["context", "manager", "async", "resource", "acquire", "release", "timeout", "generator"],
            "hint": "Document the async context manager, resource lifecycle, and cleanup guarantees.",
        },
    ],
}

# patterns we look for to check if the doc has some structure
STRUCTURE_PATTERNS = [
    r"\bargs\b", r"\bparameters?\b", r"\breturns?\b",
    r"\braises?\b", r"\bexample",
]


def score_doc(doc, keywords):
    """Score a doc on three axes: keywords (40%), length (40%), structure (20%)."""
    doc_lower = doc.lower()

    kw_hits = sum(1 for kw in keywords if kw.lower() in doc_lower)
    kw_score = kw_hits / max(len(keywords), 1)

    word_count = len(doc.split())
    len_score = min(word_count / 30, 1.0)

    struct_hits = sum(1 for p in STRUCTURE_PATTERNS if re.search(p, doc_lower))
    struct_score = struct_hits / len(STRUCTURE_PATTERNS)

    total = 0.4 * kw_score + 0.4 * len_score + 0.2 * struct_score
    return {
        "keyword": round(kw_score, 3),
        "length": round(len_score, 3),
        "structure": round(struct_score, 3),
        "total": round(total, 3),
    }


class APIDocEnv(Environment):

    def __init__(self):
        super().__init__()
        self.state_data = DocState()
        self.current = None
        self.level = "easy"

    def reset(self, **kwargs):
        self.state_data = DocState()
        level = kwargs.get("level", random.choice(list(TASKS.keys())))
        self.level = level
        self.current = random.choice(TASKS[level])

        return DocObservation(
            done=False,
            reward=0.0,
            code_snippet=self.current["code"],
            task_level=level,
            hint=self.current["hint"],
            expected_keywords=self.current["keywords"],
            feedback="Generate documentation for this API.",
        )

    def step(self, action: DocAction, **kwargs):
        if self.current is None:
            return DocObservation(
                done=True, reward=-1.0,
                code_snippet="", task_level=self.level,
                hint="", expected_keywords=[],
                feedback="Call reset() first.",
            )

        doc = action.generated_doc or ""
        if not isinstance(doc, str) or not doc.strip():
            return DocObservation(
                done=True, reward=-1.0,
                code_snippet=self.current["code"],
                task_level=self.level,
                hint=self.current["hint"],
                expected_keywords=self.current["keywords"],
                feedback="Empty or invalid documentation.",
            )

        scores = score_doc(doc, self.current["keywords"])
        reward = scores["total"]

        self.state_data.total_reward += reward
        self.state_data.step_count += 1

        matched = [kw for kw in self.current["keywords"] if kw.lower() in doc.lower()]
        missed = [kw for kw in self.current["keywords"] if kw.lower() not in doc.lower()]

        feedback = (
            f"Score: {reward:.2f}/1.00 | "
            f"Keywords ({scores['keyword']:.0%}): matched {matched}, missed {missed} | "
            f"Length ({scores['length']:.0%}): {len(doc.split())} words | "
            f"Structure ({scores['structure']:.0%})"
        )

        return DocObservation(
            done=True,
            reward=round(reward, 2),
            code_snippet=self.current["code"],
            task_level=self.level,
            hint=self.current["hint"],
            expected_keywords=self.current["keywords"],
            feedback=feedback,
        )

    @property
    def state(self):
        return self.state_data