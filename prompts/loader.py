import os

PROMPTS_DIR = os.path.join(os.path.dirname(__file__))


def load_prompt(name: str) -> str:
    path = os.path.join(PROMPTS_DIR, f"{name}.txt")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with open(path, "r") as f:
        return f.read().strip()
