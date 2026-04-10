import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import json
import gradio as gr
from openenv.core.env_server import create_web_interface_app
from environment import APIDocEnv, score_doc
from models import DocAction, DocObservation 

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

.gradio-container {
    font-family: 'Inter', sans-serif !important;
    max-width: 1200px !important;
}

#header-row {
    background: linear-gradient(135deg, #1e1b4b, #312e81) !important;
    border-radius: 12px !important;
    padding: 24px !important;
    margin-bottom: 16px !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
}

#header-row h1 {
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #e0e7ff !important;
    margin: 0 !important;
}

#header-row p {
    color: #a5b4fc !important;
    font-size: 13px !important;
}

#doc-editor textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
}

#submit-btn {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
}

#submit-btn:hover {
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
}

.score-box {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    margin: 3px;
}

.kw-hit {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.kw-miss {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.2);
}

.diff-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.diff-easy { background: rgba(16,185,129,0.15); color: #34d399; }
.diff-medium { background: rgba(245,158,11,0.15); color: #fbbf24; }
.diff-hard { background: rgba(239,68,68,0.15); color: #f87171; }
"""


def _badge(level):
    return f'<span class="diff-badge diff-{level}">{level}</span>'


def _kw_pills(keywords, doc):
    pills = []
    doc_l = doc.lower()
    for kw in keywords:
        cls = "kw-hit" if kw.lower() in doc_l else "kw-miss"
        mark = "✓" if kw.lower() in doc_l else "✗"
        pills.append(f'<span class="score-box {cls}">{mark} {kw}</span>')
    return " ".join(pills)


def _format_obs(obs):
    code = obs.get("code_snippet", "")
    level = obs.get("task_level", "easy")
    hint = obs.get("hint", "")
    keywords = obs.get("expected_keywords", [])

    md = f"## Task {_badge(level)}\n\n"
    if hint:
        md += f"> 💡 {hint}\n\n"
    md += f"```python\n{code}\n```\n\n"
    md += "**Expected keywords:** " + ", ".join(f"`{kw}`" for kw in keywords) + "\n"
    return md


def _format_result(obs, doc):
    keywords = obs.get("expected_keywords", [])
    level = obs.get("task_level", "easy")
    code = obs.get("code_snippet", "")

    scores = score_doc(doc, keywords)

    md = f"## Results {_badge(level)}\n\n"
    md += (
        f"| Metric | Score |\n|---|---|\n"
        f"| Keywords (40%) | {scores['keyword']:.0%} |\n"
        f"| Length (40%) | {scores['length']:.0%} |\n"
        f"| Structure (20%) | {scores['structure']:.0%} |\n"
        f"| **Total** | **{scores['total']:.0%}** |\n\n"
    )
    md += "### Keyword Breakdown\n\n" + _kw_pills(keywords, doc) + "\n\n"
    md += f"```python\n{code}\n```\n"
    return md


def build_ui(web_manager, action_fields, metadata, is_chat_env, title, quick_start_md):
    history = []

    async def on_reset(difficulty):
        try:
            data = await web_manager.reset_environment({"level": difficulty})
            obs = data.get("observation", {})
            return (
                _format_obs(obs),
                "",
                json.dumps(data, indent=2),
                "Ready — write your documentation below.",
                gr.update(interactive=True),
                gr.update(interactive=True),
            )
        except Exception as e:
            return (f"Error: {e}", "", "", str(e), gr.update(), gr.update())

    async def on_submit(doc, difficulty):
        if not doc or not doc.strip():
            return (gr.update(), gr.update(), gr.update(),
                    "Write something first!", gr.update())

        try:
            data = await web_manager.step_environment({"generated_doc": doc.strip()})
            obs = data.get("observation", {})
            reward = data.get("reward", 0)

            result_md = _format_result(obs, doc.strip())

            keywords = obs.get("expected_keywords", [])
            scores = score_doc(doc.strip(), keywords)
            history.append([
                len(history) + 1,
                obs.get("task_level", "?").upper(),
                obs.get("code_snippet", "")[:35] + "...",
                f"{scores['keyword']:.0%}",
                f"{scores['length']:.0%}",
                f"{scores['structure']:.0%}",
                f"{reward:.2f}",
            ])

            return (
                result_md,
                json.dumps(data, indent=2),
                [list(r) for r in history],
                f"Score: {reward:.2f}/1.00",
                gr.update(interactive=False),
            )
        except Exception as e:
            return (f"Error: {e}", "", gr.update(), str(e), gr.update())

    def on_state():
        try:
            return json.dumps(web_manager.get_state(), indent=2)
        except Exception as e:
            return str(e)

    with gr.Blocks(title="API Doc Generator") as demo:
        gr.HTML(f"<style>{CSS}</style>", visible=False)

        with gr.Row(elem_id="header-row"):
            gr.Markdown(
                "# 📝 API Documentation Generator\n"
                "Write docs for Python code, get scored on keywords, length & structure"
            )

        with gr.Row():
            with gr.Column(scale=1):
                difficulty = gr.Radio(
                    ["easy", "medium", "hard"], value="easy",
                    label="Difficulty",
                )
                with gr.Row():
                    reset_btn = gr.Button("🔄 Reset", variant="secondary")
                    state_btn = gr.Button("📊 State", variant="secondary")

                doc_editor = gr.Textbox(
                    label="Your Documentation",
                    placeholder="Write a docstring for the code shown on the right...",
                    lines=14, interactive=False, elem_id="doc-editor",
                )
                submit_btn = gr.Button(
                    "Submit", elem_id="submit-btn",
                    variant="primary", interactive=False,
                )
                status = gr.Textbox(
                    value="Hit Reset to get started.",
                    label="Status", interactive=False,
                )

            with gr.Column(scale=2):
                display = gr.Markdown(
                    "## 👋 Welcome\n\n"
                    "Pick a difficulty and hit **Reset** to get a code snippet.\n\n"
                    "Write documentation for it, then **Submit** to see your score.\n\n"
                    "Scoring: **Keywords 40%** · **Length 40%** · **Structure 20%**"
                )

                with gr.Accordion("History", open=False):
                    hist_table = gr.Dataframe(
                        headers=["#", "Level", "Code", "KW", "Len", "Struct", "Score"],
                        interactive=False,
                    )
                with gr.Accordion("Raw JSON", open=False):
                    raw = gr.Code(language="json", interactive=False)

        reset_btn.click(
            on_reset, [difficulty],
            [display, doc_editor, raw, status, doc_editor, submit_btn],
        )
        submit_btn.click(
            on_submit, [doc_editor, difficulty],
            [display, raw, hist_table, status, submit_btn],
        )
        state_btn.click(on_state, outputs=[raw])

    return demo


app = create_web_interface_app(
    APIDocEnv, DocAction, DocObservation,
    env_name="api-doc-env",
    gradio_builder=build_ui,
)
