from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from server.models import DocAction, DocObservation, DocState


class APIDocClient(EnvClient[DocAction, DocObservation, DocState]):

    def _step_payload(self, action: DocAction):
        return {"generated_doc": action.generated_doc}

    def _parse_result(self, payload):
        obs = payload.get("observation", {})
        return StepResult(
            observation=DocObservation(
                done=payload.get("done", False),
                reward=payload.get("reward"),
                code_snippet=obs.get("code_snippet", ""),
                task_level=obs.get("task_level", "easy"),
                hint=obs.get("hint", ""),
                expected_keywords=obs.get("expected_keywords", []),
                feedback=obs.get("feedback", ""),
            ),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload):
        return DocState(
            step_count=payload.get("step_count", 0),
            total_reward=payload.get("total_reward", 0.0),
        )