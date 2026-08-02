# MedHop GraphRAG on AMD NPU

This project runs a MedHop GraphRAG experiment through the local Lemonade
OpenAI-compatible API. Model weights are not included in this repository;
each user downloads them into their own Lemonade cache.

## Requirements

- Windows with a supported AMD NPU and Lemonade installed
- Python 3.11
- PowerShell

Create an environment and install the Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GRAPHRAG_API_KEY=lemonade` in the local `.env`. The local Lemonade API
does not use this as a cloud credential, but GraphRAG requires a non-empty
value. Never commit `.env`.

## Download models yourself

Run:

```powershell
.\scripts\download_models.ps1
```

This downloads/checks:

- `qwen3-it:4b` (API model ID: `qwen3-it-4b-FLM`)
- `embed-gemma:300m` (API model ID: `embed-gemma-300m-FLM`)

The files stay in the user's Lemonade cache outside this repository. If the
script cannot locate Lemonade automatically, pass its executable explicitly:

```powershell
.\scripts\download_models.ps1 -FlmPath 'C:\path\to\flm.exe'
```

Review and accept the upstream model licenses before downloading or using the
models.

## Run

Start the local model server in one PowerShell window:

```powershell
.\scripts\serve_models.ps1
```

In another activated environment, index the input and run a query:

```powershell
python .\run_graphrag.py index --root .
python .\run_graphrag.py query --root . --method local --query 'Your question'
```

GraphRAG generates local cache, log, and output directories. They are excluded
from Git and can be recreated.

## Repository contents

- `settings.yaml`: GraphRAG and local Lemonade API configuration
- `prompts/`: prompts used by the experiment
- `input/`: experiment documents; see the third-party notice before publishing
- `evaluate_medhop.py`: evaluation utility
- `import_to_neo4j.py`: optional Neo4j import utility
- `scripts/`: model download and serving helpers

## Licensing

- Original software code in this repository: Apache License 2.0 (`LICENSE`).
- Original project figures under `figures/`: CC BY 4.0
  (`FIGURES_LICENSE.md`).
- Model weights are not distributed and retain their upstream licenses.
- Dataset content, upstream prompts, dependencies, logos, and other third-party
  material are not relicensed; see `THIRD_PARTY_NOTICES.md`.

Do not publish `input/` or other derived dataset content until its
redistribution terms have been verified.
