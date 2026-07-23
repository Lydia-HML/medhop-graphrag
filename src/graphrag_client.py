import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GRAPHRAG_ROOT = PROJECT_ROOT / "graphrag_npu_0721"

GRAPHRAG_METHODS = ("local", "global", "drift", "basic")


def run_graphrag_query(method: str, question: str, api_key: str | None = None) -> str:
    """Run Microsoft GraphRAG CLI query against graphrag_npu_0721."""
    if method not in GRAPHRAG_METHODS:
        raise ValueError(f"Unsupported GraphRAG query method: {method}")

    root = GRAPHRAG_ROOT
    if not root.exists():
        raise FileNotFoundError(f"GraphRAG root does not exist: {root}")

    env = os.environ.copy()
    if api_key:
        env["GRAPHRAG_API_KEY"] = api_key
    elif "GRAPHRAG_API_KEY" not in env:
        env["GRAPHRAG_API_KEY"] = "local"

    command = [
        "graphrag",
        "query",
        "--root",
        str(root),
        "--method",
        method,
        question,
    ]

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )

    output = completed.stdout.strip()
    error = completed.stderr.strip()

    if completed.returncode != 0:
        details = error or output or "GraphRAG CLI failed without output."
        raise RuntimeError(details)

    return output or error or "GraphRAG CLI completed, but no answer was returned."
