"""
train.py
─────────
LoRA fine-tuning script for DeepSeek Coder 6.7B on the prepared
code-documentation dataset. Runs on DigitalOcean Gradient AI GPU.

Run:
    python finetune/train.py

Prerequisites:
    - data/train.jsonl and data/eval.jsonl exist (run prepare_dataset.py first)
    - GPU with at least 24GB VRAM (A100 recommended on Gradient AI)
    - All packages in requirements.txt installed
"""

import os
import sys
import yaml
import torch
from pathlib import Path
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM

# ─── Load Config ─────────────────────────────────────────────────────────────
CONFIG_PATH = Path("finetune/finetune_config.yaml")
if not CONFIG_PATH.exists():
    print("❌ finetune_config.yaml not found. Run from the ai/ directory.")
    sys.exit(1)

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)

MODEL_NAME = cfg["model"]["name"]
OUTPUT_DIR = cfg["training"]["output_dir"]
FINAL_DIR = cfg["training"]["final_model_dir"]


def check_gpu():
    if not torch.cuda.is_available():
        print("⚠️  No GPU detected. Fine-tuning will be extremely slow on CPU.")
        print("   Make sure you are running inside a Gradient AI GPU notebook.")
        response = input("   Continue anyway? (y/n): ").strip().lower()
        if response != "y":
            sys.exit(0)
    else:
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ GPU detected: {gpu_name} ({vram_gb:.1f} GB VRAM)")


def load_model_and_tokenizer(cfg: dict):
    """Load base model with optional 4-bit quantization to save VRAM."""
    print(f"\n📦 Loading base model: {MODEL_NAME}")
    print("   This will download ~13GB on first run. Subsequent runs use cache.\n")

    # 4-bit quantization config (saves ~50% VRAM, minimal quality loss)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=cfg["model"]["trust_remote_code"],
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=cfg["model"]["trust_remote_code"],
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    print("✅ Model and tokenizer loaded.")
    return model, tokenizer


def apply_lora(model, cfg: dict):
    """Apply LoRA adapters to the model."""
    lora_cfg = cfg["lora"]
    lora_config = LoraConfig(
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        bias=lora_cfg["bias"],
        task_type=lora_cfg["task_type"],
        target_modules=lora_cfg["target_modules"],
    )

    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)

    trainable, total = model.get_nb_trainable_parameters()
    print(f"✅ LoRA applied — Trainable params: {trainable:,} / {total:,} "
          f"({100 * trainable / total:.2f}%)")
    return model


def load_datasets(cfg: dict):
    """Load train/eval datasets from JSONL files."""
    train_file = cfg["dataset"]["train_file"]
    eval_file = cfg["dataset"]["eval_file"]

    if not Path(train_file).exists():
        print(f"❌ Training data not found: {train_file}")
        print("   Run: python finetune/prepare_dataset.py")
        sys.exit(1)

    dataset = load_dataset(
        "json",
        data_files={"train": train_file, "eval": eval_file},
    )
    print(f"✅ Datasets loaded:")
    print(f"   Train: {len(dataset['train']):,} examples")
    print(f"   Eval:  {len(dataset['eval']):,} examples")
    return dataset


def build_training_args(cfg: dict) -> TrainingArguments:
    """Build HuggingFace TrainingArguments from config."""
    t = cfg["training"]
    return TrainingArguments(
        output_dir=t["output_dir"],
        num_train_epochs=t["num_train_epochs"],
        per_device_train_batch_size=t["per_device_train_batch_size"],
        per_device_eval_batch_size=t["per_device_eval_batch_size"],
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        learning_rate=t["learning_rate"],
        weight_decay=t["weight_decay"],
        warmup_ratio=t["warmup_ratio"],
        lr_scheduler_type=t["lr_scheduler_type"],
        logging_steps=t["logging_steps"],
        evaluation_strategy="steps",
        eval_steps=t["eval_steps"],
        save_strategy="steps",
        save_steps=t["save_steps"],
        save_total_limit=t["save_total_limit"],
        load_best_model_at_end=t["load_best_model_at_end"],
        metric_for_best_model=t["metric_for_best_model"],
        report_to=t["report_to"],
        fp16=False,
        bf16=True,   # bfloat16 is more stable than fp16 for LLMs
        dataloader_num_workers=2,
        group_by_length=True,
    )


def main():
    print("=" * 60)
    print("  AutoDoc AI — Fine-tuning DeepSeek Coder with LoRA")
    print("  Platform: DigitalOcean Gradient AI")
    print("=" * 60)

    check_gpu()

    model, tokenizer = load_model_and_tokenizer(cfg)
    model = apply_lora(model, cfg)
    dataset = load_datasets(cfg)
    training_args = build_training_args(cfg)

    print("\n🚀 Starting fine-tuning...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
        dataset_text_field=cfg["dataset"]["text_field"],
        max_seq_length=cfg["training"]["max_seq_length"],
        packing=False,
    )

    trainer.train()

    print(f"\n💾 Saving final model to {FINAL_DIR}...")
    Path(FINAL_DIR).mkdir(parents=True, exist_ok=True)

    # Merge LoRA weights into base model for deployment
    print("🔀 Merging LoRA adapters with base model...")
    merged_model = trainer.model.merge_and_unload()
    merged_model.save_pretrained(FINAL_DIR)
    tokenizer.save_pretrained(FINAL_DIR)

    print(f"\n🎉 Fine-tuning complete!")
    print(f"   Final model saved to: {FINAL_DIR}")
    print(f"   Checkpoints saved to: {OUTPUT_DIR}")
    print(f"\n📌 Next step: Deploy {FINAL_DIR} to DigitalOcean Gradient AI endpoint")


if __name__ == "__main__":
    main()
