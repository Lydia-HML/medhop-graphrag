# GraphRAG 快速上手懶人包 📚

## 目錄
1. [前置作業](#前置作業)
2. [資料索引 (Indexing)](#資料索引-indexing)
3. [查詢 (Query)](#查詢-query)
4. [探索原始檔案](#探索原始檔案)
5. [常見問題與小技巧](#常見問題與小技巧)
6. [練習題目與答案](#練習題目與答案)

---

## 前置作業
```bash
# 1️⃣ 建立虛擬環境（如果尚未建立）
python3 -m venv .venv
source .venv/bin/activate

# 2️⃣ 安裝 GraphRAG 及相依套件
pip install "graphrag[all]" litellm huggingface_hub

# 3️⃣ 設定 Ollama API 金鑰（.env）
# 在 graphrag-ollama/.env 中加入:
# GRAPHRAG_API_KEY=ollama
```
> **Tip**：若使用 OpenAI 模型（如 `gpt-4o-mini`），請在 `.env` 中加入 `OPENAI_API_KEY`，並在 `settings.yaml` 調整 `model_provider: openai`。

---

## 資料索引 (Indexing)
1. **準備資料**：將文字檔放在 `graphrag-ollama/input/`（例如 `medhop_data.txt`）。
2. **執行索引**：
```bash
source .venv/bin/activate
graphrag index --root graphrag-ollama
```
   - 會依序完成 **切塊 → 實體抽取 → 關係抽取 → 社群報告**，結果會寫入 `graphrag-ollama/output/`。
3. **檢查輸出**：
```bash
ls graphrag-ollama/output
# 主要檔案：entities.parquet, relationships.parquet, community_reports.parquet, text_units.parquet
```

---

## 查詢 (Query)
GraphRAG 提供四種搜尋方式：
| 方法 | 說明 |
|------|------|
| `global` | Map‑Reduce 全域搜尋，適合廣泛問題 |
| `local`  | 只在最相關的 text‑units 內搜尋，回應較快 |
| `basic`  | 直接向量相似度檢索，返回原始段落 |
| `drift`  | 結合 local + global，適合需要背景的問題 |

### 範例指令
```bash
# 全域搜尋（最常用）
source .venv/bin/activate
graphrag query \
  --root graphrag-ollama \
  --method global \
  "請問在這批醫學紀錄中，主要探討了哪些藥物交互作用？"
```

### Python 呼叫範例
```python
from graphrag.api import GraphRAG
rag = GraphRAG(root="graphrag-ollama")
answer = rag.query(
    "請問在這批醫學紀錄中，主要探討了哪些藥物交互作用？",
    method="global"
)
print(answer)
```

---

## 探索原始檔案
| 檔案 | 用途 |
|------|------|
| `entities.parquet` | 抽取出的實體（藥物、疾病、基因等） |
| `relationships.parquet` | 實體之間的關係（如 `interacts_with`） |
| `text_units.parquet` | 原始文本切塊（每 1200 token） |
| `community_reports.parquet` | 每個社群的摘要報告（Map‑Reduce 中間產物） |

### 用 Pandas 快速檢視
```python
import pandas as pd
entities = pd.read_parquet('graphrag-ollama/output/entities.parquet')
print(entities.head())

rels = pd.read_parquet('graphrag-ollama/output/relationships.parquet')
print(rels[rels['type'] == 'interacts_with'].head())
```

---

## 常見問題與小技巧
- **查不到答案**：先確認 `output/community_reports.parquet` 是否完整，若缺少社群報告請重新執行 `graphrag index`。
- **JSON 解析錯誤**：確保 `settings.yaml` 中的 `completion_model` 為支援 JSON 輸出的模型（如 `gpt-4o-mini`）。
- **加速向量搜尋**：在 `settings.yaml` 的 `embedding_models.default_embedding_model.concurrent_requests` 調高，或改用 GPU 加速的嵌入模型。
- **自訂 Prompt**：編輯 `graphrag-ollama/prompts/*.txt`，例如 `global_search_map_system_prompt.txt` 以調整回應風格。

---

## 練習題目與答案
### 題目 1
**問**：在 MedHop 資料集中，哪兩種藥物被報告有交互作用？
**答**：`warfarin` 與 `amiodarone`（示例答案，實際依資料而定）。

### 題目 2
**問**：如何只查詢與「心血管疾病」相關的段落？
**答**：使用 `local` 方法並在問題中加入關鍵字：
```bash
graphrag query --root graphrag-ollama --method local "心血管疾病的相關研究有哪些？"
```

### 題目 3
**問**：若想取得所有抽取出的實體名稱，應該讀哪個檔案？
**答**：`entities.parquet`，可用 Pandas 讀取並列出 `entity_name` 欄位。

### 題目 4
**問**：在查詢時遇到 `Missing reports for communities` 警告，應該怎麼處理？
**答**：重新執行 `graphrag index`（或僅執行 `graphrag community-report`）以產生缺失的社群報告。

---

## 小結
1. **安裝 & 設定** → 建立虛擬環境、安裝套件、設定 API 金鑰。
2. **資料放置** → `input/` 目錄。
3. **執行索引** → `graphrag index`，產生向量與圖譜。
4. **查詢** → `graphrag query`（或 Python API）。
5. **探索** → 直接讀取 `output/*.parquet`。

祝您玩得開心，若有其他需求（例如建置簡易 Web UI、匯出 Neo4j 等），隨時告訴我！
