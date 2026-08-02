# GraphRAG Quickstart

這份 quickstart 只列最常用指令。完整教學請看 `README.md`。

## Before indexing: configure a model endpoint

The checked-in settings target a Lemonade / NPU OpenAI-compatible API:

- API base: `http://127.0.0.1:13305/api/v1`
- Chat model: `qwen3-it-4b-FLM`
- Embedding model: `embed-gemma-300m-FLM`

Windows users can use the checked-in settings. macOS users must update the
endpoint and model names as described in [`docs/platforms/macos.md`](docs/platforms/macos.md).
Start the endpoint before creating the index.

## 1. 安裝套件

需要 Python 3.10 或 3.11。先執行 `python --version`（Windows）或
`python3 --version`（macOS）確認版本。

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS (zsh/bash)**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 設定 API key

本機 API 若不檢查 key，可使用佔位值：

**Windows PowerShell**

```powershell
$env:GRAPHRAG_API_KEY="local"
```

**macOS (zsh/bash)**

```bash
export GRAPHRAG_API_KEY="local"
```

## 3. 下載並準備 MedHop input

MedHop 資料和衍生 input 不隨 repository 散布。請先執行：

```text
python scripts/download_medhop.py
python scripts/prepare_medhop.py
```

## 4. 建立 GraphRAG Index

```text
graphrag index --root graphrag_npu_0722
```

完成後主要產物會在：

- `graphrag_npu_0722/output/entities.parquet`
- `graphrag_npu_0722/output/relationships.parquet`
- `graphrag_npu_0722/output/communities.parquet`
- `graphrag_npu_0722/output/community_reports.parquet`
- `graphrag_npu_0722/output/lancedb/`

## 5. 查詢 GraphRAG

Local search 適合具體問題：

```text
graphrag query --root graphrag_npu_0722 --method local "Which biomedical entities are connected?"
```

Global search 適合總結整體資料：

```text
graphrag query --root graphrag_npu_0722 --method global "Summarize the major biomedical relationship patterns."
```

## 6. 啟動 Streamlit

```text
python -m streamlit run app.py
```

Streamlit app 會呼叫 `graphrag_npu_0722`，不是傳統向量 RAG。

Windows 的 Lemonade / AMD NPU 設定與 macOS endpoint 設定請參考
[`docs/platforms/`](docs/platforms/)。
