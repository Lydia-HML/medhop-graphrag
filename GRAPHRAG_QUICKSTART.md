# GraphRAG Quickstart

這份 quickstart 只列最常用指令。完整教學請看 `README.md`。

## 1. 啟動本機模型 API

請先確認 Lemonade / NPU OpenAI-compatible API 已在本機啟動：

- API base: `http://127.0.0.1:13305/api/v1`
- Chat model: `qwen3-it-4b-FLM`
- Embedding model: `embed-gemma-300m-FLM`

## 2. 安裝套件

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. 設定 API key

本機 API 若不檢查 key，可使用佔位值：

```powershell
$env:GRAPHRAG_API_KEY="local"
```

## 4. 建立 GraphRAG Index

```powershell
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

```powershell
graphrag query --root graphrag_npu_0722 --method local "Which biomedical entities are connected?"
```

Global search 適合總結整體資料：

```powershell
graphrag query --root graphrag_npu_0722 --method global "Summarize the major biomedical relationship patterns."
```

## 6. 啟動 Streamlit

```powershell
python -m streamlit run app.py
```

Streamlit app 會呼叫 `graphrag_npu_0722`，不是傳統向量 RAG。
