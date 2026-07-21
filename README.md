# SupplyGuard

SupplyGuard is a retrieval augmented software supply chain vulnerability triage system. It retrieves open-source security advisories and produces evidence-grounded answers about affected packages, vulnerable versions, available fixes, impact, and remediation.

## Current Project Status

The following components are currently implemented:

- OSV advisory corpus inspection
- Corpus filtering and preprocessing
- Reproducible sampling of 1,000 advisories
- Technical-text tokenization
- BM25 keyword retrieval
- Command-line BM25 search

Dense retrieval, local LLM generation, evaluation, and the final combined RAG pipeline are not yet implemented.

## Downloading the Raw OSV Data

SupplyGuard uses the official per ecosystem OSV data dumps. OSV provides each ecosystem as an `all.zip` archive containing its vulnerability records.

Download the four archives:

- [npm advisories](https://storage.googleapis.com/osv-vulnerabilities/npm/all.zip)
- [Maven advisories](https://storage.googleapis.com/osv-vulnerabilities/Maven/all.zip)
- [Go advisories](https://storage.googleapis.com/osv-vulnerabilities/Go/all.zip)
- [PyPI advisories](https://storage.googleapis.com/osv-vulnerabilities/PyPI/all.zip)

Place and rename the downloaded files as follows:

```text
data/raw/
├── npm.zip
├── Maven.zip
├── Go.zip
└── PyPI.zip