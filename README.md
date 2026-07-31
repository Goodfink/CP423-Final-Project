# SupplyGuard

SupplyGuard is a retrieval-augmented generation system for answering questions about open-source software security advisories. It compares classical BM25 retrieval with dense semantic retrieval while using the same local language model and evaluation set for both systems.

## System Overview

The project includes:

- a reproducibly sampled corpus of 1,000 OSV advisories
- BM25 keyword retrieval
- dense retrieval using `all-MiniLM-L6-v2`
- local answer generation using `Qwen/Qwen2.5-0.5B-Instruct`
- inline advisory citation instructions
- relevance filtering and insufficient-context abstention
- a no-retrieval diagnostic baseline
- factoid, multi-hop, and unanswerable evaluation questions
- shared automatic answer grading

Both RAG systems use the same corpus, Qwen model, prompt, generation settings, and evaluation questions. They differ only in the retrieval method.

## Repository Structure

```text
data/processed/
  advisories.jsonl
  corpus_manifest.jsonl
src/
  diagnostic_test.py
  preprocess.py
  test_rag_system.py
  evaluation/
    evaluation_metrics.py
    evaluation_set.json
  llm/
    answer_generation.py
    llm_setup.py
    prompt_template.py
  retrieval/
    bm25.py
    dense_retrieval.py
    tokenizer.py
evaluation_results.json
requirements.txt
```

## Setup

SupplyGuard requires Python 3.12 or later. Run commands from the repository root.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The first dense-retrieval and Qwen runs download models from Hugging Face. Later runs use the local model cache.

## Corpus

SupplyGuard uses public vulnerability records from the [OSV database](https://osv.dev/) for four ecosystems:

- Go
- Maven
- npm
- PyPI

The tracked processed corpus contains 1,000 advisories: 50 records per ecosystem per year for 2022 through 2026. Candidates are sorted before sampling, and sampling uses random seed `42`.

Records must:

- not be intentional malware advisories beginning with `MAL-`
- not be withdrawn
- have a publication date from January 1, 2022 through July 21, 2026
- identify at least one affected package
- include a summary or detailed description

Each processed record contains an advisory ID, chunk ID, aliases, ecosystem, package metadata, descriptions, affected ranges, fixed versions, severity, dates, references, and searchable retrieval text.

### Rebuilding the Corpus

The processed corpus is already tracked. To rebuild it, download the OSV `all.zip` archives:

- [Go](https://storage.googleapis.com/osv-vulnerabilities/Go/all.zip)
- [Maven](https://storage.googleapis.com/osv-vulnerabilities/Maven/all.zip)
- [npm](https://storage.googleapis.com/osv-vulnerabilities/npm/all.zip)
- [PyPI](https://storage.googleapis.com/osv-vulnerabilities/PyPI/all.zip)

Store them with these exact names:

```text
data/raw/
  go.zip
  Maven.zip
  npm.zip
  pypi.zip
```

Inspect the archives:

```bash
python src/data_inspection.py
```

Rebuild the processed files:

```bash
python -m src.preprocess
```

This writes:

```text
data/processed/advisories.jsonl
data/processed/corpus_manifest.jsonl
```

## Retrieval and Generation

BM25 uses `k1=1.5` and `b=0.75`. Dense retrieval uses normalized `all-MiniLM-L6-v2` embeddings and cosine similarity.

The pipeline initially retrieves five records, then applies method-specific relevance filtering:

- BM25 minimum score: `10.0`
- dense minimum cosine similarity: `0.44`
- BM25 relative score cutoff: `65%` of the top score
- dense relative score cutoff: `70%` of the top score
- maximum context records: `3`

Questions containing explicit CVE, GHSA, GO, or package identifiers must match the retrieved evidence. When no evidence qualifies, the system returns `I don't know` without calling the LLM.

Qwen receives the complete retrieval text of qualifying records and generates deterministically with sampling disabled.

## Running SupplyGuard

Check that the corpus, retrievers, and model load:

```bash
python src/test_rag_system.py --test-setup
```

Ask one question using both retrievers:

```bash
python src/test_rag_system.py --query "Which version fixes the vulnerability in github.com/dhowden/tag?"
```

Run an interactive dense-retrieval demo:

```bash
python src/test_rag_system.py --demo
```

Run BM25 without answer generation:

```bash
python -m src.retrieval.bm25 \
  --query "Which version fixes the vulnerability in github.com/dhowden/tag?" \
  --top_k 5
```

## Evaluation

The gold evaluation set contains 14 questions:

- 10 factoid questions
- 2 multi-hop questions
- 2 unanswerable questions

The same ten factoid questions are used for the no-retrieval diagnostic, which makes factual accuracy directly comparable across no retrieval, BM25, and dense retrieval.

Run the no-retrieval baseline:

```bash
python -u src/diagnostic_test.py
```

Run BM25 and dense RAG evaluation:

```bash
python -u src/test_rag_system.py --evaluate all
```

Both commands merge their outputs into `evaluation_results.json`. The file stores each question ID, generated answers, correctness labels, citation-accuracy labels, and retrieved document IDs for the available conditions.

### Current Results

| Condition | Shared factoids | Full evaluation | Unanswerable |
|---|---:|---:|---:|
| No retrieval | 0/10 (0%) | N/A | N/A |
| BM25 RAG | 7/10 (70%) | 10/14 (71.4%) | 2/2 (100%) |
| Dense RAG | 7/10 (70%) | 9/14 (64.3%) | 2/2 (100%) |

The current results show that retrieval substantially improves factual accuracy over the local model alone. BM25 currently performs better on the two multi-hop questions because it retains both required advisories more reliably.

## Known Limitations

- Qwen 0.5B sometimes extracts the wrong fact even when retrieval finds the correct advisory.
- Generated answers do not yet follow the inline citation instruction consistently.
- Dense retrieval currently misses one required advisory for a multi-hop question.
- Relevance thresholds should be calibrated on a separate development set before final reporting.
- Long retrieved records still require a total token-budget policy for arbitrary user queries.
