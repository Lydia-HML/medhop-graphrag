"""Convert locally downloaded MedHop document supports into GraphRAG input files."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/raw/medhop"))
    parser.add_argument("--output", type=Path, default=Path("graphrag_npu_0722/input"))
    parser.add_argument("--max-documents", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.is_dir():
        raise SystemExit(f"Dataset directory does not exist: {args.source}")
    if args.max_documents is not None and args.max_documents < 1:
        raise SystemExit("--max-documents must be at least 1")
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty output directory: {args.output}")

    try:
        from datasets import load_from_disk
    except ImportError as exc:
        raise SystemExit("Missing dependency: install requirements.txt first.") from exc

    dataset = load_from_disk(str(args.source))
    supports: dict[str, None] = {}
    for item in dataset:
        for support in item["supports"]:
            supports.setdefault(support, None)
            if args.max_documents and len(supports) >= args.max_documents:
                break
        if args.max_documents and len(supports) >= args.max_documents:
            break

    args.output.mkdir(parents=True, exist_ok=True)
    for index, support in enumerate(supports):
        (args.output / f"doc_{index:04d}.txt").write_text(support + "\n", encoding="utf-8")
    print(f"Wrote {len(supports)} documents to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

