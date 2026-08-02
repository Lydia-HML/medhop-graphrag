# Windows setup

The checked-in `graphrag_npu_0722/settings.yaml` targets a Lemonade
OpenAI-compatible API on `http://127.0.0.1:13305/api/v1`, using
`qwen3-it-4b-FLM` and `embed-gemma-300m-FLM`.

## Environment

Run from PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GRAPHRAG_API_KEY="local"
```

Start Lemonade or another compatible API before running GraphRAG. Confirm that
the endpoint exposes the chat and embedding model names configured in
`settings.yaml`.

## GraphRAG commands

Use the wrapper when a Windows Python installation has certificate-store
problems:

```powershell
python graphrag_npu_0722/run_graphrag.py index --root graphrag_npu_0722
python graphrag_npu_0722/run_graphrag.py query --root graphrag_npu_0722 --method local "your question"
```

The wrapper supplies Certifi CA certificates on Windows only. On a working
Windows installation, the standard `graphrag` command also works.

