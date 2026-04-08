from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union
from openenv_core.env_server.types import Action, Observation, State


@dataclass(kw_only=True)
class DocAction(Action):
    """What the AI agent submits — the documentation it wrote."""
    documentation: str = ""


@dataclass(kw_only=True)
class DocObservation(Observation):
    """What the AI agent sees — a code snippet to document.

    Inherited from Observation: done, reward, metadata.
    """
    code_snippet: str = ""
    task_level: str = "easy"
    hint: str = ""
    feedback: str = ""


@dataclass
class DocState(State):
    """Behind-the-scenes episode metadata.

    Inherited from State: episode_id, step_count.
    """
    current_task: str = ""
    max_steps: int = 1