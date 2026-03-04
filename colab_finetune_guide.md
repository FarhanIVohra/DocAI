# AutoDoc AI — External Fine-tuning Guide (Colab/Kaggle)

If DigitalOcean GPUs are unavailable, you can use **Google Colab (Free T4)** or **Kaggle (30h/week of P100/T4)** to fine-tune your model. This will give you the `checkpoints` and `adapter` files needed for "technical proof" in your hackathon submission.

---

## 📋 Strategy
We will use the **Unsloth** library (the fastest way to fine-tune) to train `deepseek-coder-6.7b-instruct` on code documentation tasks.

## 🚀 Step-by-Step

1. **Open a Notebook**: Go to [Colab](https://colab.research.google.com/) and make sure the "T4 GPU" runtime is active.
2. **Install Unsloth & Dependencies**:
   ```python
   # Pin specific versions to avoid current 'tokenizer' TypeError in Unsloth patches
   !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
   !pip install --no-deps "xformers<0.0.27" "trl==0.8.6" peft accelerate bitsandbytes
   ```
3. **Run the Training**:
   (The full code is below. It will download the Python dataset and train for ~60 steps as a demo).

```python
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# 1. Load Model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/deepseek-coder-6.7b-instruct-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
)

# 2. Add LoRA Adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
)

# 3. Load Data
dataset = load_dataset("code_search_net", "python", split = "train[:2000]")

def format_prompt(examples):
    texts = []
    for doc, code in zip(examples["func_documentation_string"], examples["whole_func_string"]):
        text = f"### Code:\n{code}\n\n### Docstring:\n{doc}"
        texts.append(text)
    return { "text" : texts, }

dataset = dataset.map(format_prompt, batched = True)

# 4. Train
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,       # Passing tokenizer explicitly is REQUIRED for Unsloth models
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = 2048,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 50,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        output_dir = "outputs",
    ),
)
trainer.train()

# 5. Save
model.save_pretrained("autodoc_adapter")
print("✅ Fine-tuning complete! Zip and download the 'autodoc_adapter' folder.")
```

---

## 🏆 Why do this for the Hackathon?
- **Judges Love Custom Models**: Even if you primarily use the Serverless API for the demo, having a fine-tuned "specialist" model shows significant extra effort.
- **Proof of Work**: You can upload the resulting weights to **DigitalOcean Spaces** and link to it in your Devpost.
- **Cost**: It costs $0 on Colab but adds $1,000+ of perceived value to your stack.

## 🛠️ Troubleshooting: `TypeError: got an unexpected keyword argument 'tokenizer'`
If you still see this error even with `trl==0.8.6`, it means `unsloth`'s monkey-patch for the Trainer is conflicting with a newer version of `transformers` pre-installed in Colab.

**The Fix**:
Change your first cell to include a `transformers` pin as well:
```python
!pip install --no-deps "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps "xformers<0.0.27" "trl==0.8.6" "transformers<4.41.0" peft accelerate bitsandbytes
```
Then **Restart Runtime** and run all cells.
