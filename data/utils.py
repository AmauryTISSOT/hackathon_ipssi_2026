from pathlib import Path


def get_project_root():
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / ".env").exists():
            return parent
    return current_path.parent


def safe(x):
    return x if x is not None else ""