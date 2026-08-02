"""Download a MedHop split to a local, Git-ignored Hugging Face dataset cache."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="bigbio/medhop")
    parser.add_argument("--config", default="medhop_source")
    parser.add_argument("--split", default="train", choices=("train", "validation"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/medhop"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite existing dataset directory: {args.output}")

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise SystemExit("Missing dependency: install requirements.txt first.") from exc

    dataset = load_dataset(args.dataset, args.config, split=args.split)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(str(args.output))
    print(f"Saved {len(dataset)} {args.split} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

