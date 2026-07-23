# MedHop GraphRAG

這是一個以 `graphrag_npu_0721/` 為核心的 Microsoft GraphRAG 教學專案。使用者會從 MedHop 生醫文本開始，自己執行 GraphRAG index，產生 entity graph、relationships、communities、community reports 與向量索引，最後再透過 GraphRAG CLI 或 Streamlit 介面查詢。

目前主線如下：

```text
MedHop 生醫文本
  -> GraphRAG input/
  -> graphrag index
  -> output/ indexed artifacts
  -> graphrag query
  -> Streamlit 問答介面
```

本專案主流程是 Microsoft GraphRAG。傳統 Vector RAG / ChromaDB 查詢流程已移除，避免和 GraphRAG 架構混在一起。

## 快速啟動

### 1. 進入專案資料夾

```powershell
cd "C:\Users\labpc\OneDrive\文件\Medhop\medhop-graphrag"
```

### 2. 安裝套件

```powershell
pip install -r requirements.txt
```

### 3. 設定 GraphRAG API Key

GraphRAG CLI 需要讀取 `GRAPHRAG_API_KEY`。如果本機 Lemonade / NPU API 不檢查 key，可以先用：

```powershell
$env:GRAPHRAG_API_KEY="local"
```

### 4. 確認本機模型 API 已啟動

目前 `graphrag_npu_0721/settings.yaml` 指向：

```text
http://127.0.0.1:13305/api/v1
```

使用的模型名稱：

```text
completion model: qwen3-it-4b-FLM
embedding model: embed-gemma-300m-FLM
```

請先確認 Lemonade / NPU 的 OpenAI-compatible API server 已經啟動，且模型名稱和 `settings.yaml` 一致。

### 5. 建立 GraphRAG index

第一次使用，或拿到尚未包含 `output/` 的專案時，需要先執行 index：

```powershell
graphrag index --root graphrag_npu_0721
```

這一步會呼叫 completion model 與 embedding model，時間會比查詢更久。完成後會產生：

```text
graphrag_npu_0721/output/
```

### 6. 用 CLI 查詢

index 完成後再查詢：

```powershell
graphrag query --root graphrag_npu_0721 --method local "What genes are related to the disease evidence in this dataset?"
```

如果有成功輸出答案，代表 GraphRAG index、GraphRAG CLI 與本機模型 API 都已經接上。

### 7. 啟動 Streamlit 介面

```powershell
python -m streamlit run app.py
```

Streamlit 介面只是包裝 GraphRAG CLI。它查詢的是 `graphrag_npu_0721/output/` 中由 `graphrag index` 產生的 indexed artifacts。

## 使用前檢查

### 執行 index 前必須存在

| 項目 | 路徑 |
|---|---|
| Streamlit app | `app.py` |
| GraphRAG client | `src/graphrag_client.py` |
| GraphRAG root | `graphrag_npu_0721/` |
| GraphRAG 設定 | `graphrag_npu_0721/settings.yaml` |
| 輸入文本 | `graphrag_npu_0721/input/` |
| Prompt templates | `graphrag_npu_0721/prompts/` |
| 套件清單 | `requirements.txt` |

### 執行 index 後才會產生

| 項目 | 路徑 |
|---|---|
| Documents | `graphrag_npu_0721/output/documents.parquet` |
| Text units | `graphrag_npu_0721/output/text_units.parquet` |
| Entities | `graphrag_npu_0721/output/entities.parquet` |
| Relationships | `graphrag_npu_0721/output/relationships.parquet` |
| Communities | `graphrag_npu_0721/output/communities.parquet` |
| Community reports | `graphrag_npu_0721/output/community_reports.parquet` |
| Graph snapshot | `graphrag_npu_0721/output/graph.graphml` |
| Vector index | `graphrag_npu_0721/output/lancedb/` |

如果 `output/` 不存在，請先執行：

```powershell
graphrag index --root graphrag_npu_0721
```

## 你會用到的三個指令

### 建立 index

```powershell
graphrag index --root graphrag_npu_0721
```

### 查詢

```powershell
graphrag query --root graphrag_npu_0721 --method local "your question"
```

### 開啟網頁介面

```powershell
python -m streamlit run app.py
```

建議順序是：

```text
先 index
再 query
最後視需要開 Streamlit
```

## 專案結構

```text
medhop-graphrag/
|-- app.py                         # Streamlit UI，呼叫 GraphRAG CLI
|-- requirements.txt               # Python 套件
|-- README.md                      # 本文件
|-- PROJECT_STRUCTURE.md           # 專案整理筆記
|-- GRAPHRAG_QUICKSTART.md         # GraphRAG 快速筆記
|-- explore_medhop.py              # 探索 MedHop dataset
|-- src/
|   |-- __init__.py
|   `-- graphrag_client.py         # Python 呼叫 graphrag query 的 wrapper
|-- medhop/
|   |-- medhop.py                  # MedHop dataset script
|   |-- bigbiohub.py
|   `-- README.md                  # MedHop dataset card
`-- graphrag_npu_0721/
    |-- settings.yaml              # GraphRAG root 設定
    |-- input/                     # GraphRAG input text
    |-- prompts/                   # GraphRAG prompt templates
    |-- output/                    # 執行 graphrag index 後產生
    |-- run_graphrag_cli.py        # CLI 輔助 script
    |-- medhop_graph_tools.py      # GraphRAG / MedHop helper
    |-- openai_neo4j_utils.py      # OpenAI-compatible API 與 Neo4j helper
    |-- import_to_neo4j.py         # 匯入 Neo4j 的輔助工具
    |-- graph_visualization.png    # 圖視覺化圖片
    `-- medhop_graphrag.ipynb      # Notebook 實驗
```

## GraphRAG 架構介紹

這個專案使用 Microsoft GraphRAG。整體流程如下：

```text
MedHop text input
  -> chunking
  -> entity extraction
  -> relationship extraction
  -> graph construction
  -> community detection
  -> community reports
  -> vector indexes
  -> GraphRAG query
```

GraphRAG 和傳統 RAG 最大差異是：它不只是把文件切成 chunks 後做 vector search，而是先把資料整理成 entity graph，再用圖上的關係與 community reports 支援回答。

### Input

GraphRAG 從這裡讀文字：

```text
graphrag_npu_0721/input/
```

目前共有 5 個輸入文件：

```text
doc_0000.txt
doc_0001.txt
doc_0002.txt
doc_0003.txt
doc_0004.txt
```

這些檔案會被 GraphRAG 當成原始文件來源。

### Chunking

設定在 `graphrag_npu_0721/settings.yaml`：

```yaml
chunking:
  type: tokens
  size: 450
  overlap: 60
  encoding_model: cl100k_base
```

| 參數 | 說明 |
|---|---|
| `size: 450` | 每個 text unit 約 450 tokens |
| `overlap: 60` | 相鄰 chunk 重疊 60 tokens |
| `encoding_model: cl100k_base` | 用這個 tokenizer 估算 token |

執行 index 後會產生：

```text
graphrag_npu_0721/output/text_units.parquet
```

### Entity 與 Relationship 抽取

GraphRAG 使用 LLM 從 text units 抽取生醫實體與關係。

設定：

```yaml
extract_graph:
  completion_model_id: default_completion_model
  prompt: prompts/extract_graph.txt
  entity_types:
    - BIOMEDICAL_ENTITY
    - GENE
    - PROTEIN
    - DISEASE
    - DRUG
    - CHEMICAL
    - VARIANT
    - PHENOTYPE
    - BIOMARKER
    - PATHWAY
    - BIOLOGICAL_PROCESS
    - ORGANISM
  max_gleanings: 0
```

Entity 可以理解成圖上的節點，例如 gene、protein、disease、drug。Relationship 可以理解成節點之間的邊，例如某個 gene 和 disease 之間的關聯。

執行 index 後會產生：

```text
graphrag_npu_0721/output/entities.parquet
graphrag_npu_0721/output/relationships.parquet
graphrag_npu_0721/output/raw_entities.parquet
graphrag_npu_0721/output/raw_relationships.parquet
```

### Community

GraphRAG 會把 entity graph 做社群偵測。這裡的核心演算法是 Leiden community detection。

Leiden 是 Louvain community detection 的改良版，用來在圖上找出連結密度高的節點群。對 GraphRAG 來說，community 可以把一群相關的藥物、疾病、基因、蛋白質或 pathway 整理成較高層次的知識單元。

設定：

```yaml
cluster_graph:
  max_cluster_size: 10
  seed: 42
```

執行 index 後會產生：

```text
graphrag_npu_0721/output/communities.parquet
```

### Community Reports

Community reports 是 GraphRAG 很重要的一層。GraphRAG 會針對每個 community 產生摘要，讓後續查詢不只看單一 chunk，而是可以看一整群相關節點的整理結果。

設定：

```yaml
community_reports:
  completion_model_id: default_completion_model
  graph_prompt: prompts/community_report_graph.txt
  text_prompt: prompts/community_report_text.txt
  max_length: 600
  max_input_length: 4000
```

執行 index 後會產生：

```text
graphrag_npu_0721/output/community_reports.parquet
```

### Vector Store

GraphRAG 會建立 LanceDB 向量索引，用於 text units、entity descriptions 與 community content 的檢索。

設定：

```yaml
vector_store:
  type: lancedb
  db_uri: output/lancedb
  index_schema:
    text_unit_text:
      vector_size: 768
    entity_description:
      vector_size: 768
    community_full_content:
      vector_size: 768
```

執行 index 後會產生：

```text
graphrag_npu_0721/output/lancedb/
```

## Query Method 怎麼選

| Method | 適合情境 |
|---|---|
| `local` | 問特定 entity、gene、disease、drug、evidence |
| `global` | 問整體趨勢、主題摘要、資料集總覽 |
| `drift` | 從一個局部問題延伸到相關主題 |
| `basic` | 基礎查詢，可當作對照 |

建議新手先這樣用：

```text
特定生醫問題 -> local
整體資料摘要 -> global
不知道該用哪個 -> local
```

## 微調數值介紹

以下參數都在：

```text
graphrag_npu_0721/settings.yaml
```

### 1. 併發數

```yaml
concurrent_requests: 1
```

| 數值 | 說明 |
|---:|---|
| `1` | 最穩，適合本機 NPU / Lemonade |
| `2` 以上 | 可能加快，但也可能造成 API 壓力 |

建議新手先維持 `1`。

### 2. Completion Model

```yaml
completion_models:
  default_completion_model:
    type: litellm
    model_provider: openai
    model: qwen3-it-4b-FLM
    api_base: http://127.0.0.1:13305/api/v1
    call_args:
      temperature: 0
      timeout: 300
```

| 參數 | 目前值 | 說明 |
|---|---|---|
| `model` | `qwen3-it-4b-FLM` | 生成模型 |
| `temperature` | `0` | 輸出穩定度 |
| `timeout` | `300` | 單次呼叫等待秒數 |

建圖建議維持 `temperature: 0`，輸出會比較穩定。

### 3. Embedding Model 與 Vector Size

```yaml
embedding_models:
  default_embedding_model:
    model: embed-gemma-300m-FLM
```

```yaml
vector_store:
  index_schema:
    text_unit_text:
      vector_size: 768
    entity_description:
      vector_size: 768
    community_full_content:
      vector_size: 768
```

| 參數 | 說明 |
|---|---|
| `embed-gemma-300m-FLM` | embedding model |
| `vector_size: 768` | 必須等於 embedding model 的輸出維度 |

如果換 embedding model，一定要確認 vector size 是否相同，並重新執行 index。

### 4. Chunk 大小

```yaml
chunking:
  size: 450
  overlap: 60
```

| 調整方向 | 可能影響 |
|---|---|
| 增加 `size` | 單一 chunk 上下文更多，但 LLM 負擔增加 |
| 減少 `size` | chunk 更細，但關係可能被切散 |
| 增加 `overlap` | 降低重要資訊被切斷的機率，但資料量變多 |

新手建議先不要動。若關係抽得太碎，可試：

```yaml
size: 600
overlap: 80
```

### 5. Entity Types

```yaml
entity_types:
  - BIOMEDICAL_ENTITY
  - GENE
  - PROTEIN
  - DISEASE
  - DRUG
  - CHEMICAL
  - VARIANT
  - PHENOTYPE
  - BIOMARKER
  - PATHWAY
  - BIOLOGICAL_PROCESS
  - ORGANISM
```

MedHop 是 biomedical multi-hop QA，所以 `GENE`、`PROTEIN`、`DISEASE`、`DRUG` 通常要保留。

### 6. max_gleanings

```yaml
extract_graph:
  max_gleanings: 0
```

`max_gleanings` 控制 GraphRAG 是否追加抽取更多 entities / relationships。

| 數值 | 說明 |
|---:|---|
| `0` | 最快、最穩 |
| `1` | 可能抽更多關係 |
| `2` 以上 | 可能增加召回，但本機模型壓力大 |

目前設為 `0` 是為了本機 NPU 穩定。

### 7. Community 大小

```yaml
cluster_graph:
  max_cluster_size: 10
```

| 調整方向 | 可能影響 |
|---|---|
| 變小 | community 更細，局部關係更明確 |
| 變大 | community 更概括，global summary 可能更完整 |

### 8. Community Report 長度

```yaml
community_reports:
  max_length: 600
  max_input_length: 4000
```

| 參數 | 目前值 | 說明 |
|---|---:|---|
| `max_length` | `600` | 報告輸出長度 |
| `max_input_length` | `4000` | 產生報告時可讀的上下文 |

### 9. Local Search

```yaml
local_search:
  max_context_tokens: 2400
  top_k_entities: 6
  top_k_relationships: 8
```

| 參數 | 說明 |
|---|---|
| `max_context_tokens` | 查詢時塞給 LLM 的 context 上限 |
| `top_k_entities` | 取回相關 entities 的數量 |
| `top_k_relationships` | 取回相關 relationships 的數量 |

如果回答太短或找不到資訊，可以小幅提高 `top_k_entities` 或 `top_k_relationships`，然後重新查詢。這類 query 參數通常不需要重新 index。

### 10. Global Search

```yaml
global_search:
  max_context_tokens: 2400
```

Global search 更適合問整體摘要。若模型常常回空或超時，可以降低 `max_context_tokens`；若模型能力足夠，可以提高。

## 常見問題

### Q1. Streamlit 查詢失敗怎麼辦？

先確認：

1. Lemonade / NPU API server 是否啟動。
2. `GRAPHRAG_API_KEY` 是否設定。
3. `graphrag` 指令是否可執行。
4. 是否已先執行 `graphrag index --root graphrag_npu_0721`。
5. `graphrag_npu_0721/output/` 是否已產生。
6. `settings.yaml` 的 model name 是否和 API server 註冊名稱一致。

### Q2. 什麼時候要重新 index？

下列情況需要重新 index：

1. 第一次使用，專案還沒有 `output/`。
2. 修改 `input/` 文字。
3. 修改 prompt。
4. 修改 entity types。
5. 換 completion model。
6. 換 embedding model。
7. 修改 chunking、entity extraction、community 或 embedding 設定。

只是問新問題，不需要重新 index。

### Q3. 換 embedding model 後壞掉？

請確認：

1. 新 embedding model 的輸出維度。
2. `vector_size` 是否同步修改。
3. 舊的 `output/lancedb/` 是否需要重建。
4. 是否已重新執行 `graphrag index --root graphrag_npu_0721`。

### Q4. 可以先刪掉 output 讓使用者自己跑嗎？

可以。只要保留 `settings.yaml`、`input/`、`prompts/` 與必要程式碼，使用者就能重新執行：

```powershell
graphrag index --root graphrag_npu_0721
```

完成後再查詢：

```powershell
graphrag query --root graphrag_npu_0721 --method local "your question"
```

## Neo4j 輔助工具

Neo4j 不是本專案的 GraphRAG 核心，只是用來承接 GraphRAG outputs 做查圖或視覺化。

相關檔案：

```text
graphrag_npu_0721/import_to_neo4j.py
graphrag_npu_0721/openai_neo4j_utils.py
graphrag_npu_0721/medhop_graph_tools.py
```

GraphRAG 會先產生 parquet / LanceDB / GraphML，之後才視需求匯入 Neo4j。

## 一句話總結

新手使用時，只要記住這條主線：

```text
啟動 Lemonade / NPU API
-> 設定 GRAPHRAG_API_KEY
-> graphrag index --root graphrag_npu_0721
-> graphrag query --root graphrag_npu_0721
-> 或 python -m streamlit run app.py
```

## 設備與環境要求

### 必要

| 項目 | 建議 |
|---|---|
| Python | 3.10 或 3.11 |
| GraphRAG CLI | `graphrag` 指令需可執行 |
| Lemonade / NPU API | OpenAI-compatible API server |
| Completion model | `qwen3-it-4b-FLM` |
| Embedding model | `embed-gemma-300m-FLM` |
| Embedding vector size | `768` |

### 目前設定的 API endpoint

```text
http://127.0.0.1:13305/api/v1
```
