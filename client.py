from dataclasses import asdict
from openenv_core.http_env_client import HTTPEnvClient
from openenv_core.client_types import StepResult
from models import DocAction, DocObservation, DocState


class DocEnv(HTTPEnvClient[DocAction, DocObservation]):
    """
    Client for the API Documentation Generator environment.

    Usage:
        env = DocEnv(base_url="https://YOUR_SPACE.hf.space")
        result = env.reset()
        print(result.observation.code_snippet)

        result = env.step(DocAction(documentation="My docs here..."))
        print(f"Score: {result.reward}")

        env.close()
    """

    def _step_payload(self, action: DocAction) -> dict:
        """Convert action → JSON to send over HTTP."""
        return {"documentation": action.documentation}

    def _parse_result(self, payload: dict) -> StepResult:
        """Convert JSON response → typed StepResult."""
        obs_data = payload.get("observation", {})
        return StepResult(
            observation=DocObservation(
                done=payload.get("done", False),
                reward=payload.get("reward"),
                code_snippet=obs_data.get("code_snippet", ""),
                task_level=obs_data.get("task_level", "easy"),
                hint=obs_data.get("hint", ""),
                feedback=obs_data.get("feedback", ""),
            ),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> DocState:
        """Convert JSON → typed DocState."""
        return DocState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            current_task=payload.get("current_task", ""),
            max_steps=payload.get("max_steps", 1),
        )