from pathlib import Path


def decide_file_type(file_path: Path) -> str:
    """Return "pdf" if the file is a PDF, otherwise "html".
    This simple check avoids any LLM calls or extra configuration.
    """
    return "pdf" if file_path.suffix.lower() == ".pdf" else "html"
