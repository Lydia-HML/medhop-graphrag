import json
import os
import sys

try:
    from datasets import load_dataset
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
    from datasets import load_dataset

def main():
    print("Loading medhop dataset...")
    # Load dataset using the local script
    ds = load_dataset("./medhop/medhop.py", name="medhop_source")
    
    print("Dataset splits:", ds.keys())
    
    train_ds = ds['train']
    print(f"Train split size: {len(train_ds)}")
    
    if len(train_ds) > 0:
        example = train_ds[0]
        print("\nExample 0 keys:", example.keys())
        print(f"Query: {example['query']}")
        print(f"Number of supports: {len(example['supports'])}")
        print(f"Answer: {example['answer']}")
        print(f"First support snippet: {example['supports'][0][:200]}")
    
    # Let's count total unique supports
    unique_supports = set()
    for row in train_ds:
        for sup in row['supports']:
            unique_supports.add(sup)
            
    print(f"\nTotal unique supports in train: {len(unique_supports)}")

if __name__ == "__main__":
    main()
