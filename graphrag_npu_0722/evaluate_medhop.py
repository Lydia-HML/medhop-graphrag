"""Evaluate GraphRAG answers on BigBio MedHop multiple-choice questions."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path


DRUGBANK_ID = re.compile(r"(?<![A-Z0-9])DB\d{5}(?![A-Z0-9])", re.IGNORECASE)
DATA_CITATION = re.compile(r"\[Data:\s*(.*?)\]", re.IGNORECASE | re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--split", default="train", choices=("train", "validation"))
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--method", default="local", choices=("local", "global", "drift", "basic"))
    parser.add_argument("--timeout", type=int, default=300, help="Seconds allowed per query")
    parser.add_argument("--output", type=Path, default=Path("medhop_evaluation.csv"))
    parser.add_argument("--dataset-cache", type=Path, help="Optional Hugging Face datasets cache directory")
    return parser.parse_args()


def build_prompt(item: dict) -> str:
    candidates = ", ".join(item["candidates"])
    return (
        "Answer this MedHop multiple-choice question. Follow multi-hop relationships in the "
        "evidence. Select exactly one candidate and return only its DrugBank ID.\n"
        f"Question: {item['query']}\n"
        f"Candidates: {candidates}"
    )


def extract_prediction(response: str, candidates: list[str]) -> tuple[str, str]:
    """Return (prediction, parse_status), accepting only an unambiguous candidate."""
    normalized = {candidate.upper() for candidate in candidates}
    lines = [line.strip() for line in response.splitlines() if line.strip()]

    # Prefer a model that obeyed the requested output contract.
    if lines and re.fullmatch(r"DB\d{5}[.!]?", lines[0], re.IGNORECASE):
        answer = DRUGBANK_ID.search(lines[0]).group(0).upper()
        if answer in normalized:
            return answer, "exact_first_line"

    # Exclude GraphRAG citations, whose numeric IDs can otherwise pollute parsing.
    answer_text = DATA_CITATION.sub("", response)
    mentions = [match.group(0).upper() for match in DRUGBANK_ID.finditer(answer_text)]
    unique_candidates = list(dict.fromkeys(x for x in mentions if x in normalized))
    if len(unique_candidates) == 1:
        return unique_candidates[0], "single_candidate_mention"
    if not unique_candidates:
        return "", "no_candidate"
    return "", "ambiguous_candidates"


def run_query(root: Path, method: str, prompt: str, timeout: int) -> tuple[str, str, float]:
    command = [
        sys.executable,
        str(root / "run_graphrag.py"),
        "query",
        "--root",
        str(root),
        "--method",
        method,
        prompt,
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        elapsed = time.perf_counter() - started
        if completed.returncode != 0:
            error = completed.stderr.strip() or f"exit_code={completed.returncode}"
            return completed.stdout.strip(), error, elapsed
        return completed.stdout.strip(), "", elapsed
    except subprocess.TimeoutExpired as exc:
        elapsed = time.perf_counter() - started
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return stdout.strip(), f"timeout_after_{timeout}s", elapsed


def load_items(split: str, cache_dir: Path | None):
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Missing dependency: install/import the 'datasets' package in this environment.") from exc
    kwargs = {"cache_dir": str(cache_dir)} if cache_dir else {}
    return load_dataset("bigbio/medhop", "medhop_source", **kwargs)[split]


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    dataset = load_items(args.split, args.dataset_cache)
    stop = min(args.start + args.limit, len(dataset))
    if args.start < 0 or args.limit < 1 or args.start >= len(dataset):
        raise SystemExit("Invalid --start/--limit for selected split")

    fieldnames = [
        "id", "question", "candidates", "gold_answer", "predicted_answer",
        "exact_match", "parse_status", "method", "latency_seconds", "citations",
        "error", "response",
    ]
    correct = 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for position in range(args.start, stop):
            item = dataset[position]
            response, error, latency = run_query(
                root, args.method, build_prompt(item), args.timeout
            )
            prediction, parse_status = extract_prediction(response, item["candidates"])
            gold = item["answer"].upper()
            match = int(not error and prediction == gold)
            correct += match
            citations = " | ".join(x.strip() for x in DATA_CITATION.findall(response))
            writer.writerow({
                "id": item["id"],
                "question": item["query"],
                "candidates": json.dumps(item["candidates"], ensure_ascii=False),
                "gold_answer": gold,
                "predicted_answer": prediction or "NONE",
                "exact_match": match,
                "parse_status": parse_status,
                "method": args.method,
                "latency_seconds": f"{latency:.3f}",
                "citations": citations,
                "error": error,
                "response": response,
            })
            handle.flush()
            print(
                f"[{position + 1}/{stop}] {item['id']}: gold={gold} "
                f"pred={prediction or 'NONE'} EM={match} ({latency:.1f}s)",
                flush=True,
            )

    evaluated = stop - args.start
    print(f"\nExact match: {correct}/{evaluated} = {correct / evaluated:.2%}")
    print(f"Results: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
