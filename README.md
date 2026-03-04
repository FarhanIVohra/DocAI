# AutoDoc AI — AI Layer 🚀

> **DigitalOcean Gradient™ AI Hackathon** | Member 1 (AI/ML Track)

This directory contains the AI infrastructure for AutoDoc AI. It uses **DigitalOcean Gradient AI Serverless Inference** for high-performance code analysis and documentation generation.

---

## 🏗️ Architecture

The AI layer is organized into modular services in `ai/services/`:

- **`llm_service.py`**: Wrapper for DO Gradient AI (OpenAI-compatible).
- **`embedder.py`**: CodeBERT-based vectorization (768-dim) + ChromaDB.
- **`repo_indexer.py`**: GitHub cloning and AST-based code chunking.
- **`rag_service.py`**: Retrieval-Augmented Generation pipeline.
- **`doc_generator.py`**: Orchestrates 6 doc types (README, API, Diagram, **Audit**, etc.).
- **`chat_agent.py`**: Stateful conversational agent with repository context.
- **`commit_assistant.py`**: ⭐️ **Elite**: AI utility to write professional git commit messages.

---

## 🛠️ Setup

### 1. Configure Environment
1. Copy `.env.example` to `.env`.
2. Get your **Model Access Key** from the [DigitalOcean Cloud Console](https://cloud.digitalocean.com/gradient/serverless-inference).
3. Update `.env`:
```env
GRADIENT_ENDPOINT_URL=https://inference.do-ai.run/v1
GRADIENT_MODEL_ACCESS_KEY=your_key_here
GRADIENT_MODEL=llama3.3-70b-instruct
```

### 2. Verify Services
Run the following to ensure all services are ready:
```bash
python -c "from services.llm_service import get_llm; get_llm()"
python -c "from services.embedder import get_embedder; get_embedder()"
```

---

## 🤖 AI Stack Details

| Component | Technology |
|---|---|
| **LLM** | `llama3.3-70b-instruct` (Serverless Inference) |
| **Embeddings** | `microsoft/codebert-base` (HuggingFace) |
| **Vector DB** | ChromaDB (Persistent local storage) |
| **Code Parsing** | `tree-sitter` (AST analysis) |
| **Platform** | DigitalOcean Gradient AI |

---

## 📡 Backend Integration (Next Steps)

Member 2 (Backend/Frontend) should call the services in this order:
1. `RepoIndexer.index_repo(url, job_id)` -> Indexes the repo into ChromaDB.
2. `DocGenerator.generate(type, job_id, meta)` -> Returns Markdown documentation.
3. `ChatAgent(job_id).chat(message)` -> Returns stateful AI response with sources.
4. `DocGenerator.generate("audit", job_id)` -> ⭐️ **Elite**: Security & Health Audit.

---

## ⭐️ Elite AI Utilities

### AI Commit Assistant
Tired of writing `git commit -m "fix"`?
```bash
# Stage your changes
git add .
# Generate a professional message
python services/commit_assistant.py
```
Outputs a perfect Conventional Commit message with emojis!

---

## 📊 Training Evidence
While we use Serverless for production, the `finetune/` directory contains complete scripts for fine-tuning models on Gradient AI GPUs as part of our technical design.
