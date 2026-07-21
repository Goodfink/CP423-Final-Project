# SupplyGuard

SupplyGuard is a retrieval augmented software supply chain vulnerability triage system. It retrieves open source security advisories and produces evidence grounded answers about affected packages, vulnerable versions, available fixes, impact, and remediation.

## Current Project Status

The following components are currently implemented:

- OSV advisory corpus inspection
- Corpus filtering and preprocessing
- Reproducible sampling of 1000 advisories
- Technical text tokenization
- BM25 keyword retrieval
- Command line BM25 search

## Data Source

SupplyGuard uses official vulnerability records from the [OSV database](https://osv.dev/).

The corpus includes advisories from four software ecosystems:

- npm
- Maven
- Go
- PyPI

## Downloading the Raw OSV Data

OSV provides each ecosystem as an `all.zip` archive containing its vulnerability records.

Download the four archives:

- [npm advisories](https://storage.googleapis.com/osv-vulnerabilities/npm/all.zip)
- [Maven advisories](https://storage.googleapis.com/osv-vulnerabilities/Maven/all.zip)
- [Go advisories](https://storage.googleapis.com/osv-vulnerabilities/Go/all.zip)
- [PyPI advisories](https://storage.googleapis.com/osv-vulnerabilities/PyPI/all.zip)

Place and rename the downloaded files as follows:

```
data/raw/
├── npm.zip
├── Maven.zip
├── Go.zip
└── PyPI.zip
```

The raw archives are excluded from Git because they are large and may change as OSV is updated.

The processed corpus and manifest preserve the exact 1000 advisories used by the project.

## Corpus Construction

The preprocessing pipeline keeps advisories that:

- are not intentional malware records beginning with `MAL-`
- have not been withdrawn
- were published between January 1, 2022 and July 21, 2026
- contain at least one affected package
- contain either a summary or detailed description

Valid advisories are grouped by ecosystem and publication year.

The pipeline selects:

- 50 advisories per year
- 5 years from 2022 through 2026
- 4 ecosystems

This creates a balanced corpus of:

```
50 × 5 × 4 = 1000 advisories
```

Sampling uses the fixed random seed `42`.

Candidates are sorted by advisory ID before sampling to ensure reproducible results.

## Processed Files

The preprocessing pipeline generates:

```
data/processed/
├── advisories.jsonl
└── corpus_manifest.json
```

### `advisories.jsonl`

Each line contains one normalized advisory with fields including:

- document ID
- chunk ID
- advisory ID
- aliases
- ecosystem
- affected packages
- summary
- details
- affected version ranges
- fixed versions
- severity
- publication date
- references
- retrieval text

The `retrieval_text` field combines the advisory information that should be searchable by the retrieval systems.

### `corpus_manifest.json`

The corpus manifest records:

- random seed
- publication date range
- included years
- number of samples per year
- total number of documents
- selected advisory IDs
- ecosystem and publication year for each advisory

## Running the Project

Run all commands from the project root:

```
CP423-Final-Project/
```

The project currently uses Python 3.12.

Depending on the system configuration, `python` may need to be replaced with `python3` or the full path to Python 3.12.

### 1. Inspect the Raw Dataset

The inspection script reports statistics about each raw OSV archive.

Run:

```bash
python -m src.data_inspection
```

The script reports:

- total JSON records
- GHSA records
- malicious records
- withdrawn records
- records within the publication date range
- records with affected packages
- records with descriptions
- valid candidate records

The inspection script does not modify the raw data or generate the processed corpus.

### 2. Build the Processed Corpus

Run:

```bash
python -m src.preprocess
```

The preprocessing script:

1. Opens each OSV ZIP archive.
2. Reads the JSON vulnerability records.
3. Applies the advisory validation rules.
4. Groups valid advisories by ecosystem and year.
5. selects 50 advisories from every ecosystem and year.
6. Normalizes the selected records.
7. Builds the searchable `retrieval_text` field.
8. Writes the processed corpus and manifest.

Expected output:

```
Saved 1000 processed advisories
```

Generated files:

```
data/processed/advisories.jsonl
data/processed/corpus_manifest.json
```

### 3. Run BM25 Retrieval

Run a BM25 search from the project root:

```bash
python -m src.retrieval.bm25 \
  --query "Which version fixes the vulnerability in github.com/dhowden/tag?" \
  --top_k 5
```

The command returns the top-ranked advisory records with:

- rank
- BM25 score
- document ID
- chunk ID
- advisory summary

Example result:

```
Rank: 1
Score: 12.7738
Document ID: GHSA-27mh-3343-6hg5
Chunk ID: GHSA-27mh-3343-6hg5_chunk_0
Summary: dhowden tag panic due to out-of-bounds read
```