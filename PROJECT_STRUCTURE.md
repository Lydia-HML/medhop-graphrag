# MedHop GraphRAG Project Structure

This repository is now centered on `graphrag_npu_0721/` as the main GraphRAG path:

1. Microsoft GraphRAG-style indexing/querying over the MedHop biomedical multi-hop QA dataset.
2. A Streamlit app that calls `graphrag query --root graphrag_npu_0721`.

## Top-Level Files

| Path | Purpose |
| --- | --- |
| `app.py` | Streamlit app that calls GraphRAG CLI over `graphrag_npu_0721`. |
| `requirements.txt` | Python dependencies. Note that this file currently mixes app dependencies, GraphRAG dependencies, and generated environment packages. |
| `README.md` | Main Chinese project readme. |
| `explore_medhop.py` | Utility script to load and inspect the MedHop dataset. |
| `GRAPHRAG_QUICKSTART.md` | Quickstart for indexing/querying `graphrag_npu_0721`. |

## App Code

| Path | Purpose |
| --- | --- |
| `src/graphrag_client.py` | Wraps `graphrag query --root graphrag_npu_0721` for the Streamlit app. |

## MedHop Dataset

| Path | Purpose |
| --- | --- |
| `medhop/README.md` | Dataset card for MedHop. |
| `medhop/medhop.py` | Hugging Face datasets loader for MedHop. |
| `medhop/bigbiohub.py` | BigBio schema helpers used by the dataset loader. |
| `medhop/.env.example` | Example environment file. |

## GraphRAG Runs

| Path | Purpose |
| --- | --- |
| `graphrag_npu_0721/` | GraphRAG root configured for a local NPU/Lemonade OpenAI-compatible API. |
| `graphrag_npu_0721/settings.yaml` | GraphRAG configuration using `qwen3-it-4b-FLM` and `embed-gemma-300m-FLM`. |
| `graphrag_npu_0721/medhop_graph_tools.py` | Helper utilities for MedHop/GraphRAG analysis. |
| `graphrag_npu_0721/import_to_neo4j.py` | Script for importing generated graph data into Neo4j. |
| `graphrag_npu_0721/run_graphrag_cli.py` | Small runner for GraphRAG tasks. |
| `graphrag_npu_0721/medhop_graphrag.ipynb` | Notebook for GraphRAG experimentation. |
| `graphrag_npu_0721/output/` | Generated GraphRAG outputs, including entities, relationships, text units, communities, and graph snapshots. |

## Generated Or Machine-Specific Content

These files/directories are generated or local-environment specific and should normally not be committed in a clean project:

| Path | Why |
| --- | --- |
| `.venv/`, `hf_venv/` | Local virtual environments. |
| `__pycache__/`, `src/__pycache__/` | Python bytecode cache. |
| `.DS_Store` files | macOS Finder metadata. |
| `graphrag-*/cache*/` | GraphRAG cache data. |
| `graphrag-*/logs*/` | GraphRAG logs. |
| `graphrag-*/output*/` | Generated GraphRAG outputs; keep only if you need reproducible artifacts. |

## Is This Microsoft GraphRAG?

Yes, the GraphRAG parts use the Microsoft GraphRAG project/package style:

- `requirements.txt` includes `graphrag==3.0.8` and related `graphrag-*` packages.
- `graphrag_npu_0721/settings.yaml` uses the Microsoft GraphRAG YAML layout: `completion_models`, `embedding_models`, `input_storage`, `output_storage`, `cache`, `vector_store`, `extract_graph`, `cluster_graph`, `community_reports`, `local_search`, and `global_search`.

However, the whole repository is not only the upstream Microsoft GraphRAG example. It combines:

- Microsoft GraphRAG indexing/query experiments using a local NPU/Lemonade OpenAI-compatible model server,
- MedHop dataset utilities, and
- Neo4j import/analysis helpers.


