"""
prepare_dataset.py
──────────────────
Downloads the CodeSearchNet Python dataset from HuggingFace, filters for
high-quality code→docstring pairs, formats them into instruction-tuning
format, and saves to data/train.jsonl + data/eval.jsonl.

Run:
    python finetune/prepare_dataset.py

Output:
    data/train.jsonl  (~15,000 examples)
    data/eval.jsonl   (~2,000 examples)
"""

import json
import os
import re
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

# ─── Config ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("./data")
TRAIN_FILE = OUTPUT_DIR / "train.jsonl"
EVAL_FILE = OUTPUT_DIR / "eval.jsonl"
MAX_TRAIN = 15_000
MAX_EVAL = 2_000
MIN_DOCSTRING_LEN = 50       # Filter out trivial one-liners
MIN_CODE_LEN = 50            # Filter out trivial functions
MAX_CODE_LEN = 2_000         # Avoid huge functions that exceed context


INSTRUCTION_TEMPLATES = [
    "Write comprehensive documentation for this Python function:",
    "Generate a detailed docstring for the following Python code:",
    "Document this Python function with description, parameters, and return value:",
    "Create professional API documentation for this function:",
    "Write a clear docstring explaining what this Python function does:",
]


def clean_docstring(docstring: str) -> str:
    """Strip leading/trailing whitespace and normalize indentation."""
    lines = docstring.strip().splitlines()
    cleaned = [line.strip() for line in lines]
    return "\n".join(cleaned).strip()


def clean_code(code: str) -> str:
    """Remove existing docstrings from the function body for clean training."""
    # Remove triple-quoted docstrings at start of function body
    pattern = r'(def\s+\w+[^:]+:)\s*"""[\s\S]*?"""'
    code = re.sub(pattern, r"\1", code)
    pattern = r"(def\s+\w+[^:]+:)\s*'''[\s\S]*?'''"
    code = re.sub(pattern, r"\1", code)
    return code.strip()


def is_quality_pair(code: str, docstring: str) -> bool:
    """Filter out low-quality training pairs."""
    if len(docstring) < MIN_DOCSTRING_LEN:
        return False
    if len(code) < MIN_CODE_LEN or len(code) > MAX_CODE_LEN:
        return False
    # Skip generic/placeholder docstrings
    blacklist = ["todo", "fixme", "placeholder", "not implemented", "pass"]
    if any(word in docstring.lower() for word in blacklist):
        return False
    # Must have a real function definition
    if not code.strip().startswith("def "):
        return False
    return True


def format_example(code: str, docstring: str, idx: int) -> dict:
    """Format a single code+docstring pair into instruction-tuning format."""
    instruction = INSTRUCTION_TEMPLATES[idx % len(INSTRUCTION_TEMPLATES)]
    clean_doc = clean_docstring(docstring)
    clean_src = clean_code(code)

    # Full formatted text for SFTTrainer
    text = (
        f"### Instruction:\n{instruction}\n\n"
        f"### Code:\n```python\n{clean_src}\n```\n\n"
        f"### Documentation:\n{clean_doc}"
    )

    return {
        "instruction": instruction,
        "input": clean_src,
        "output": clean_doc,
        "text": text,
    }


def process_split(examples: list, max_count: int) -> list:
    """Process and filter a dataset split."""
    results = []
    for i, example in enumerate(tqdm(examples, desc="Processing")):
        code = example.get("func_code_string", "") or example.get("whole_func_string", "")
        docstring = example.get("func_documentation_string", "")

        if not code or not docstring:
            continue
        if not is_quality_pair(code, docstring):
            continue

        results.append(format_example(code, docstring, i))

        if len(results) >= max_count:
            break

    return results


def save_jsonl(data: list, path: Path) -> None:
    """Save list of dicts to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  ✅ Saved {len(data):,} examples → {path}")


def main():
    print("🔽 Downloading CodeSearchNet (Python split) from HuggingFace...")
    print("   This may take a few minutes on first run.\n")

    dataset = load_dataset(
        "code_search_net",
        "python",
        trust_remote_code=True,
    )

    print(f"\n📊 Dataset sizes:")
    print(f"   Train split: {len(dataset['train']):,} examples")
    print(f"   Valid split: {len(dataset['validation']):,} examples")
    print(f"   Test split:  {len(dataset['test']):,} examples\n")

    print(f"🔧 Processing training set (target: {MAX_TRAIN:,} examples)...")
    train_data = process_split(list(dataset["train"]), MAX_TRAIN)

    print(f"\n🔧 Processing eval set (target: {MAX_EVAL:,} examples)...")
    eval_data = process_split(list(dataset["validation"]), MAX_EVAL)

    print(f"\n💾 Saving datasets...")
    save_jsonl(train_data, TRAIN_FILE)
    save_jsonl(eval_data, EVAL_FILE)

    print(f"\n🎉 Dataset preparation complete!")
    print(f"   Train: {len(train_data):,} examples  →  {TRAIN_FILE}")
    print(f"   Eval:  {len(eval_data):,} examples   →  {EVAL_FILE}")
    print(f"\n📌 Next step: python finetune/train.py")


if __name__ == "__main__":
    main()
