# macOS setup

The Python application and GraphRAG workflow are shared with Windows. The
checked-in model settings target Lemonade's Windows/NPU endpoint, so macOS
users must provide an OpenAI-compatible chat and embedding endpoint and update
the model names and `api_base` values in `graphrag_npu_0722/settings.yaml` to
match it.

## Environment

Run from zsh or bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GRAPHRAG_API_KEY="local"
```

Use the API key required by your selected endpoint instead of `local` when
authentication is enabled.

## Model endpoint

Before indexing, verify that the selected endpoint provides:

- a chat/completions model for entity extraction, summaries, and answers;
- an embedding model whose vector dimension matches `vector_size` in
  `settings.yaml` (the current value is `768`);
- OpenAI-compatible chat and embedding APIs.

Do not commit local endpoint URLs, credentials, model weights, input documents,
or GraphRAG output.

## GraphRAG commands

```bash
python scripts/download_medhop.py
python scripts/prepare_medhop.py
graphrag index --root graphrag_npu_0722
graphrag query --root graphrag_npu_0722 --method local "your question"
python -m streamlit run app.py
```

The `run_graphrag.py` wrapper is not required on macOS because it only applies
the Windows certificate-store workaround.

