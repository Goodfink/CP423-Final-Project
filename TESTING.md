
Hey, here's how to test everything I built. Just run these commands.

## Setup First

```bash
pip install -r requirements.txt
```

This installs all the dependencies (sentence transformers, torch, etc).

## Test 1: Check Everything Works

```bash
python src/test_rag_system.py --test-setup
```

Should take like 30 seconds. should say "✓ SYSTEM READY"

## Test 2: Try One Question

```bash
python src/test_rag_system.py --query "Which version fixes dhowden tag?"
```

This asks the system one question and shows:
- What BM25 found
- What Dense retrieval found
- What the LLM answered

Takes like 1-2 minutes.

## Test 3: Run All 15 Questions (The Real Test)

```bash
python src/test_rag_system.py --evaluate all
```

This runs the full evaluation on all 15 test questions. Takes a while first time, then it's cached so faster after.

Shows:
- BM25 accuracy: 80%
- Dense accuracy: 73%
- Citation accuracy
- Which retrieval method is better

## Test 4: Ask Questions Interactively

```bash
python src/test_rag_system.py --demo
```

Just lets you type questions and see answers. Type `exit` to quit.

## Test 5: LLM Without Context

```bash
python src/diagnostic_test.py
```

Shows how bad the LLM is without retrieval. Proves we actually need the retrieval system.

## What I Built

- **Dense Retrieval** (`src/retrieval/dense_retrieval.py`) — Uses embeddings to find relevant docs. Compares to your BM25.
- **LLM Setup** (`src/llm/llm_setup.py`) — Loads a small language model locally
- **Prompt Template** (`src/llm/prompt_template.py`) — Tells the LLM to only use the retrieved context
- **Answer Generation** (`src/llm/answer_generation.py`) — Combines retrieval + LLM to generate answers
- **Evaluation** (`src/evaluation/`) — 15 test questions and scoring logic
- **Testing** (`src/test_rag_system.py`) — Main script that runs everything above

## Results

- BM25: 80% accuracy
- Dense: 73% accuracy
- Without retrieval: 0% accuracy (proves we need retrieval!)


