from openenv.core.env_server import Action, Observation, State


class DocAction(Action):
    generated_doc: str


class DocObservation(Observation):
    code_snippet: str
    task_level: str
    hint: str
    expected_keywords: list[str]
    feedback: str


class DocState(State):
    total_reward: float = 0.0