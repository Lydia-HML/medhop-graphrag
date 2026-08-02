# MedHop GraphRAG 教材

這份專案以 `graphrag_npu_0722/` 作為主要 GraphRAG 範例，示範如何使用 Microsoft GraphRAG、MedHop 生醫多跳問答資料，以及 Lemonade / NPU OpenAI-compatible API 建立知識圖譜索引，並透過 CLI 或 Streamlit 進行查詢。

MedHop 是從 Medline/PubMed 摘要建構的生醫多跳問答資料集，題目聚焦在藥物之間的交互作用，需要跨多篇文件串接藥物與蛋白質反應鏈來推理答案。這很適合作為 GraphRAG 教材，因為它能展示「從文字抽取實體關係，再用圖譜輔助多跳查詢」的流程。

本版主軸只保留 GraphRAG 流程，Streamlit 介面會呼叫 GraphRAG CLI，不另外混用其他檢索管線。

## 教材資源

- 教學簡報：[AMD AIPC MedHop GraphRAG](https://gamma.app/docs/AMD-AIPC-MedHop-GraphRAG--ck9fdgg1feyy6u1?mode=doc)
- Demo 影片：[YouTube Demo](https://youtu.be/n04f6Txv7yU)

```text
MedHop text
-> graphrag_npu_0722/input/
-> graphrag index
-> graphrag_npu_0722/output/
-> graphrag query
-> Streamlit UI
```

## 快速啟動

### 1. 進入專案

**Windows PowerShell**

```powershell
cd "C:\Users\labpc\OneDrive\文件\Medhop\medhop-graphrag"
```

**macOS (zsh/bash)**

```bash
cd /path/to/medhop-graphrag
```

### 2. 建立環境並安裝套件

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

### 3. 設定 API key

本機 Lemonade / NPU API 如果不檢查 key，可以先使用佔位值：

**Windows PowerShell**

```powershell
$env:GRAPHRAG_API_KEY="local"
```

**macOS (zsh/bash)**

```bash
export GRAPHRAG_API_KEY="local"
```

### 4. 確認本機模型 API

`graphrag_npu_0722/settings.yaml` 預設連到：

```text
API base: http://127.0.0.1:13305/api/v1
Chat model: qwen3-it-4b-FLM
Embedding model: embed-gemma-300m-FLM
```

請先確認 Lemonade 或相容的 OpenAI API server 已啟動，且模型名稱與設定檔一致。
Windows 的 AMD NPU/Lemonade 設定與 macOS 的替代 endpoint 請分別參考
[Windows 指南](docs/platforms/windows.md) 與 [macOS 指南](docs/platforms/macos.md)。

### 5. 下載並準備 MedHop 資料

MedHop 及其衍生的 GraphRAG input 不隨本 repository 散布。請先自行下載資料集，再準備本機 input：

```text
python scripts/download_medhop.py
python scripts/prepare_medhop.py
```

這些指令會將原始資料存於 `data/raw/medhop/`，並把文件寫入
`graphrag_npu_0722/input/`。兩個位置都已被 Git 忽略。

### 6. 建立 GraphRAG index

```text
graphrag index --root graphrag_npu_0722
```

完成後會產生：

```text
graphrag_npu_0722/output/
```

### 7. 使用 CLI 查詢

```text
graphrag query --root graphrag_npu_0722 --method local "What genes are related to the disease evidence in this dataset?"
```

### 8. 啟動 Streamlit 介面

```text
python -m streamlit run app.py
```

Streamlit 會固定使用 `graphrag_npu_0722` 作為 GraphRAG root。

## 專案結構

### 主要檔案

| 路徑 | 說明 |
|---|---|
| `README.md` | 主要中文上手教學。 |
| `GRAPHRAG_QUICKSTART.md` | 精簡版 GraphRAG 指令。 |
| `PROJECT_STRUCTURE.md` | 專案檔案結構說明。 |
| `app.py` | Streamlit 查詢介面。 |
| `src/graphrag_client.py` | GraphRAG CLI 呼叫封裝。 |
| `requirements.txt` | Python 套件需求。 |

### GraphRAG 教材資料夾

| 路徑 | 說明 |
|---|---|
| `graphrag_npu_0722/settings.yaml` | Microsoft GraphRAG 設定檔。 |
| `graphrag_npu_0722/input/` | 本機由 MedHop 資料準備的 GraphRAG indexing 輸入文字，不隨 repository 散布。 |
| `graphrag_npu_0722/prompts/` | GraphRAG 使用的 prompt templates。 |
| `graphrag_npu_0722/output/` | 本機 indexing 後的 graph、table、vector index 產物，不隨 repository 散布。 |
| `graphrag_npu_0722/evaluate_medhop.py` | MedHop multiple-choice 評估腳本。 |
| `graphrag_npu_0722/import_to_neo4j.py` | 將 GraphRAG 產物匯入 Neo4j 的輔助腳本。 |
| `graphrag_npu_0722/run_graphrag.py` | GraphRAG 執行輔助腳本。 |

## GraphRAG 架構介紹

GraphRAG 不是只把文件切 chunk 後做向量搜尋。它會先把文件轉成圖結構，再同時使用實體、關係、社群摘要與文字片段回答問題。

下圖可以搭配本段一起看：左半部是建立 index 的流程，右半部是查詢時會用到的資料結構與 GraphRAG query。

![MedHop GraphRAG 架構圖](assets/architecture-graphrag.svg)

圖中的流程對應到本專案如下：

| 圖中階段 | 專案對應 | 說明 |
|---|---|---|
| MedHop | `data/raw/medhop/`、`graphrag_npu_0722/input/` | MedHop 是原始生醫多跳問答資料；使用者下載後，GraphRAG 讀取本機 `input/` 內的文字檔。 |
| 文字前處理 | `explore_medhop.py`、資料整理流程 | 將資料集內容整理成適合 GraphRAG indexing 的純文字輸入。 |
| Chunk | `settings.yaml` 的 `chunking` 設定 | GraphRAG 依照 chunk size 與 overlap 將文件切成 text units。 |
| Qwen3 生醫圖譜抽取 | `completion_models`、`prompts/extract_graph.txt` | 使用本機 Qwen3 模型抽取 entities 與 relationships，形成知識圖譜。 |
| Leiden 社群偵測 | `cluster_graph` | GraphRAG 在產生 community reports 之前，會先使用 Leiden community detection 將圖分群。 |
| Community Reports | `community_reports` | 使用 LLM 針對每個 community 產生摘要報告，讓 global/local query 可以引用社群層級脈絡。 |
| Embed-Gemma 向量化 | `embedding_models` | 使用 `embed-gemma-300m-FLM` 將文字、實體描述與 community content 向量化；此模型對應 Google EmbeddingGemma 類型的輕量文字 embedding model，官方定位是 retrieval、semantic search、RAG 等用途。 |
| LanceDB / GraphML | `output/lancedb/`、`output/graph.graphml` | LanceDB 儲存向量索引，GraphML 保存圖結構快照。 |
| GraphRAG Query | `graphrag query`、`app.py` | CLI 或 Streamlit 會讀取已建立好的 index，依 query method 組合圖譜與文字脈絡回答。 |

Indexing 流程：

```text
input documents
-> token chunking
-> entity extraction
-> relationship extraction
-> graph construction
-> Leiden community detection
-> community reports
-> LanceDB vector indexes
```

主要演算法與元件：

| 階段 | 說明 |
|---|---|
| Chunking | 將輸入文件切成 text units，讓 LLM 可以穩定處理。 |
| Entity extraction | 使用 LLM 從 text units 抽取生醫實體。 |
| Relationship extraction | 使用 LLM 抽取實體之間的關係與描述。 |
| Graph construction | 將 entities 與 relationships 組成 knowledge graph。 |
| Community detection | GraphRAG 使用 Leiden community detection 將圖分群。 |
| Community reports | 使用 LLM 替每個 community 產生摘要報告。 |
| Vector index | 使用 LanceDB 儲存 text units、entity descriptions、community content 等 embedding。 |

Query 流程：

```text
question
-> GraphRAG query method
-> retrieve graph/text/community context
-> local LLM API
-> answer
```

## Query Method 怎麼選

| Method | 適合情境 |
|---|---|
| `local` | 具體問題，例如某個 gene、drug、disease、evidence 之間的關係。 |
| `global` | 想總結整份資料的主題、趨勢或大型關係模式。 |
| `drift` | 從問題出發，沿著相關實體與 community 擴展脈絡。 |
| `basic` | 較單純的文字與向量脈絡查詢。 |

教材示範建議先使用 `local`，因為 MedHop 題目通常需要在局部生醫實體關係中找證據。

## MedHop 評估設計提醒

MedHop 原始任務是 multiple-choice QA：題目通常會給定一個查詢與多個候選答案，系統需要跨文件推理後選出正解，最後用 exact match 評分。

GraphRAG 原本更偏向 query-focused summarization，也就是針對開放式問題組合圖譜、社群摘要與文字脈絡後生成答案。因此做 MedHop 評估時，不應只看模型自由生成的長答案，而要明確設計「候選答案選擇」流程：

1. 對每個候選答案建立同格式 prompt，要求模型只輸出候選選項或答案字串。
2. 使用 `local` 或 `drift` 查詢補足多跳證據，再讓模型在候選答案中做選擇。
3. 將輸出正規化後再和標準答案做 exact match。
4. 保留 GraphRAG 回答與引用脈絡，方便檢查錯誤是來自 retrieval、圖譜抽取、community report，還是最後選項判斷。

## 重要參數微調

設定檔位於 `graphrag_npu_0722/settings.yaml`。

| 參數 | 目前值 | 調整方向 |
|---|---|---|
| `concurrent_requests` | `1` | NPU 或本機模型不穩時維持 1；硬體較強時可逐步增加。 |
| `chunking.size` | `450` | 越大保留越多上下文，但抽取成本與錯誤風險會增加。 |
| `chunking.overlap` | `60` | 避免跨 chunk 資訊斷裂；太高會增加索引成本。 |
| `completion model` | `qwen3-it-4b-FLM` | 負責抽取、摘要與回答。 |
| `embedding model` | `embed-gemma-300m-FLM` | 負責向量化文字與圖譜描述。 |
| `vector_size` | `768` | 必須與 embedding model 輸出維度一致。 |
| `top_k_entities` | `6` | Local search 取回的相關實體數。 |
| `top_k_relationships` | `20` | Local search 取回的關係數；多跳問題可適度提高。 |
| `max_context_tokens` | `2400` | 回答時可使用的上下文長度；太高會增加延遲。 |

## 重新跑 Index 前要檢查什麼

1. `graphrag_npu_0722/input/` 內是否有要索引的文字檔。
2. Lemonade / NPU API 是否已啟動。
3. `settings.yaml` 的 `api_base`、模型名稱、embedding 維度是否正確。
4. `GRAPHRAG_API_KEY` 是否已設定。
5. 若要完全重建結果，可先移除舊的 `output/`、`cache/`、`logs/` 後再執行 `graphrag index`。

## 評估腳本

0722 資料夾內含 MedHop multiple-choice 評估腳本：

```powershell
python graphrag_npu_0722/evaluate_medhop.py --method local --limit 5
```

輸出檔案：

```text
graphrag_npu_0722/medhop_evaluation.csv
```

## 常見問題

### 查詢失敗

請依序確認：

1. Lemonade / NPU API 是否正在執行。
2. `GRAPHRAG_API_KEY` 是否已設定。
3. `graphrag` CLI 是否安裝在目前 Python 環境。
4. `graphrag_npu_0722/output/` 是否已建立。
5. `settings.yaml` 的模型名稱是否與本機 API 提供的名稱一致。

### 改了 input 後需要重跑 index 嗎？

需要。GraphRAG 的 entities、relationships、communities、community reports 與 LanceDB 都是 indexing 的產物。只要輸入文件、prompt、模型或 chunking 設定有變，就建議重新執行：

```powershell
graphrag index --root graphrag_npu_0722
```

## 設備需求

| 項目 | 建議 |
|---|---|
| OS | Windows 11 或 macOS |
| Python | 3.10 或 3.11 |
| GraphRAG CLI | `graphrag` |
| Local API | Lemonade / NPU OpenAI-compatible API |
| Completion model | `qwen3-it-4b-FLM` |
| Embedding model | `embed-gemma-300m-FLM` |
| Memory | 至少 16 GB RAM，較大資料建議 32 GB 以上。 |
| Accelerator | Windows 可使用 AMD NPU / GPU；macOS 使用相容的本機或遠端 OpenAI-compatible endpoint。 |

## License

Original source code in this repository is licensed under the Apache License
2.0. Different terms apply to third-party datasets, model weights, runtimes,
and educational media. In particular:

- MedHop data and derived data: CC BY-SA 3.0
- Microsoft GraphRAG: MIT License
- Qwen3 model weights: Apache License 2.0
- EmbeddingGemma: Google Gemma Terms of Use
- Lemonade runtime: Apache License 2.0
- Original diagrams and teaching materials: CC BY 4.0 unless otherwise stated

MedHop data, model weights, and GraphRAG-generated artifacts are not
distributed with this repository. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
and [data/README.md](data/README.md) for attribution and usage details.
