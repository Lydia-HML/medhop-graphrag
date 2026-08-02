# MedHop GraphRAG Project Structure

本專案目前以 `graphrag_npu_0722/` 作為主要 GraphRAG 教材與執行資料夾，搭配 Streamlit 介面示範如何查詢已建立好的 MedHop biomedical knowledge graph。

## Top-Level Files

| Path | Purpose |
| --- | --- |
| `README.md` | 主要中文上手教學，包含快速啟動、架構介紹、參數微調與設備需求。 |
| `GRAPHRAG_QUICKSTART.md` | 精簡版 GraphRAG CLI 快速指令。 |
| `app.py` | Streamlit 查詢介面，透過 `src/graphrag_client.py` 呼叫 GraphRAG CLI。 |
| `requirements.txt` | Python 套件需求。 |
| `explore_medhop.py` | MedHop 資料集檢查工具。 |
| `scripts/download_medhop.py` | 將使用者自行取得的 MedHop split 快取到本機。 |
| `scripts/prepare_medhop.py` | 將本機 MedHop supports 轉成 GraphRAG input 文件。 |
| `data/README.md` | MedHop 資料的授權、引用與本機準備說明。 |

## App Code

| Path | Purpose |
| --- | --- |
| `src/graphrag_client.py` | 封裝 `graphrag query --root graphrag_npu_0722`，供 Streamlit app 使用。 |

## MedHop Dataset

| Path | Purpose |
| --- | --- |
| `medhop/README.md` | MedHop dataset card。 |
| `medhop/medhop.py` | Hugging Face datasets loader。 |
| `medhop/bigbiohub.py` | BigBio schema helper。 |
| `medhop/.env.example` | 環境變數範例。 |

## GraphRAG Root

| Path | Purpose |
| --- | --- |
| `graphrag_npu_0722/` | 主要 GraphRAG root，設定 Lemonade / NPU OpenAI-compatible API。 |
| `graphrag_npu_0722/settings.yaml` | Microsoft GraphRAG 設定檔，包含模型、輸入、輸出、向量資料庫與搜尋參數。 |
| `graphrag_npu_0722/input/` | 從本機 MedHop 資料準備的 indexing 輸入文件；不提交至 Git。 |
| `graphrag_npu_0722/prompts/` | Entity extraction、summarization、community report 等 prompt。 |
| `graphrag_npu_0722/output/` | GraphRAG 產出的 entities、relationships、communities、community reports、LanceDB 等結果；不提交至 Git。 |
| `graphrag_npu_0722/evaluate_medhop.py` | MedHop 評估腳本。 |
| `graphrag_npu_0722/import_to_neo4j.py` | 將 GraphRAG 產物匯入 Neo4j 的輔助腳本。 |
| `graphrag_npu_0722/run_graphrag.py` | GraphRAG 執行輔助腳本。 |

## Generated Or Local Content

這些通常是本機或重新 indexing 後產生的內容，不一定適合提交到 Git：

| Path | Why |
| --- | --- |
| `.venv/`, `hf_venv/`, `venv/` | 本機 Python virtual environment。 |
| `__pycache__/` | Python bytecode cache。 |
| `.DS_Store`, `Thumbs.db` | 作業系統 metadata。 |
| `graphrag_*/cache*/` | GraphRAG cache。 |
| `graphrag_*/logs*/` | GraphRAG logs。 |
| `graphrag_*/output*/` | GraphRAG indexing/query 產物；教材若要讓使用者重跑，可不提交這類資料。 |
| `data/raw/`, `data/processed/` | 使用者下載的 MedHop 資料及其本機衍生副本。 |

## Is This Microsoft GraphRAG?

是。`graphrag_npu_0722/settings.yaml` 採用 Microsoft GraphRAG 的設定結構，例如：

- `completion_models`
- `embedding_models`
- `input_storage`
- `output_storage`
- `vector_store`
- `extract_graph`
- `cluster_graph`
- `community_reports`
- `local_search`
- `global_search`

這份 repo 不是單純複製 upstream 範例，而是把 Microsoft GraphRAG 套到 MedHop biomedical QA 教材，並加入 Streamlit 查詢介面、NPU/Lemonade 本機模型設定與 Neo4j/評估輔助工具。
