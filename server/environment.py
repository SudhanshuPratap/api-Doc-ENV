import uuid
import random
from openenv_core.env_server.interfaces import Environment
from models import DocAction, DocObservation, DocState


# ── The 3 tasks (easy → medium → hard) ───────────────────────────────────────

TASKS = {
    "easy": {
        "code": """\
def add_numbers(a: int, b: int) -> int:
    return a + b
""",
        "hint": "Describe what this function does, its parameters, and what it returns.",
        "required_keywords": ["param", "return", "int", "add"],
        "description": "Simple function with two inputs",
    },

    "medium": {
        "code": """\
class BankAccount:
    def __init__(self, owner: str, balance: float = 0.0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount: float) -> None:
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
""",
        "hint": "Document the class, __init__, deposit, and withdraw. Include the ValueError.",
        "required_keywords": ["param", "raises", "owner", "balance", "deposit", "withdraw"],
        "description": "Class with multiple methods and error handling",
    },

    "hard": {
        "code": """\
import asyncio
from functools import wraps


def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator
""",
        "hint": "Explain the retry decorator, its parameters, exponential backoff, and async behavior.",
        "required_keywords": ["param", "decorator", "async", "retry", "attempts", "backoff"],
        "description": "Async decorator with exponential backoff",
    },
}


# ── Environment class ─────────────────────────────────────────────────────────

class DocEnvironment(Environment):
    """
    API Documentation Generator Environment.

    An AI agent receives a Python code snippet and must write
    clear, accurate documentation for it. The grader checks
    completeness, keyword coverage, and structure.
    """

    def __init__(self):
        super().__init__(transform=None)
        self._state = DocState()
        self._current_level = "easy"

    # ── reset() ──────────────────────────────────────────────────────────────

    def reset(self, **kwargs) -> DocObservation:
        """Start a new episode. Picks a task level randomly."""
        task_level = kwargs.get("task_level")
        episode_id = kwargs.get("episode_id")

        self._current_level = task_level or random.choice(["easy", "medium", "hard"])
        task = TASKS[self._current_level]

        self._state = DocState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            current_task=self._current_level,
            max_steps=1,
        )

        return DocObservation(
            done=False,
            reward=None,
            code_snippet=task["code"],
            task_level=self._current_level,
            hint=task["hint"],
            feedback="",
        )

    # ── step() ───────────────────────────────────────────────────────────────

    def step(self, action: DocAction) -> DocObservation:
        """Grade the agent's documentation. Each episode is one step."""
        self._state.step_count += 1
        task = TASKS[self._current_level]

        score, feedback = self._grade(
            docs=action.documentation,
            required_keywords=task["required_keywords"],
            task_level=self._current_level,
        )

        return DocObservation(
            done=True,
            reward=score,
            code_snippet=task["code"],
            task_level=self._current_level,
            hint=task["hint"],
            feedback=feedback,
        )

    # ── state ────────────────────────────────────────────────────────────────

    @property
    def state(self) -> DocState:
        """Return episode metadata."""
        return self._state

    # ── grader ───────────────────────────────────────────────────────────────

    def _grade(self, docs: str, required_keywords: list, task_level: str):
        """
        Score documentation on 3 axes:
          40% — length (is it detailed enough?)
          40% — keyword coverage (does it mention important concepts?)
          20% — structure (does it have Args/Returns sections?)

        Returns (score: float 0.0–1.0, feedback: str)
        """
        if not docs or len(docs.strip()) < 20:
            return 0.0, "Documentation is too short or empty."

        docs_lower = docs.lower()
        breakdown = []

        # ── 40%: Length score ─────────────────────────────
        min_length = {"easy": 80, "medium": 200, "hard": 300}[task_level]
        length_score = min(len(docs.strip()) / min_length, 1.0) * 0.4
        breakdown.append(f"Length: {length_score:.2f}/0.40")

        # ── 40%: Keyword coverage ─────────────────────────
        hits = [kw for kw in required_keywords if kw in docs_lower]
        keyword_score = (len(hits) / len(required_keywords)) * 0.4
        missed = [kw for kw in required_keywords if kw not in docs_lower]
        breakdown.append(f"Keywords: {keyword_score:.2f}/0.40 (missing: {missed or 'none'})")

        # ── 20%: Structure ────────────────────────────────
        structure_words = ["args:", "arguments:", "returns:", "raises:", "example:", "param", ":param", "parameters"]
        has_structure = any(w in docs_lower for w in structure_words)
        structure_score = 0.2 if has_structure else 0.0
        breakdown.append(f"Structure: {structure_score:.2f}/0.20")

        total = round(min(length_score + keyword_score + structure_score, 1.0), 2)
        feedback = f"Score {total:.2f} | " + " | ".join(breakdown)

        return total, feedback