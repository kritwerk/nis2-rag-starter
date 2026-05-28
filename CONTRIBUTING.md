# Contributing

Danke fürs Reinschauen. Dieses Repo ist eine **Demo** — Issues und kleine
PRs sind willkommen, größere Feature-Vorschläge bitte vorher per Issue
abstimmen.

## Setup

```bash
git clone https://github.com/kritwerk/nis2-rag-starter.git
cd nis2-rag-starter
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,openai]"
```

## Vor dem PR

```bash
ruff check src tests
mypy src
pytest
```

## Stil

- Python 3.11+, Typ-Annotationen Pflicht (mypy strict).
- Kommerziell sensible Kunden-Daten **nie** committen.
- Keine echten NIS2/KRITIS-Quelltexte ins Repo — Lizenzfragen.
