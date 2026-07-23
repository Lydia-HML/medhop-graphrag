# graphrag_npu_0721 快速上手

這份專案目前以 `graphrag_npu_0721/` 為主要 GraphRAG root。它使用 Microsoft GraphRAG，並對接本機 Lemonade / NPU OpenAI-compatible API。

## 1. 確認模型服務

`graphrag_npu_0721/settings.yaml` 目前設定：

```yaml
completion_models:
  default_completion_model:
    model: qwen3-it-4b-FLM
    api_base: http://127.0.0.1:13305/api/v1

embedding_models:
  default_embedding_model:
    model: embed-gemma-300m-FLM
    api_base: http://127.0.0.1:13305/api/v1
```

執行前請先確認 Lemonade / NPU API server 已啟動。

## 2. 設定 API Key

如果本機 API 不檢查 key，可以用任意值：

```powershell
$env:GRAPHRAG_API_KEY="local"
```

## 3. 建立索引

```bash
graphrag index --root graphrag_npu_0721
```

Index 會產生：

- `graphrag_npu_0721/output/text_units.parquet`
- `graphrag_npu_0721/output/entities.parquet`
- `graphrag_npu_0721/output/relationships.parquet`
- `graphrag_npu_0721/output/communities.parquet`
- `graphrag_npu_0721/output/community_reports.parquet`
- `graphrag_npu_0721/output/lancedb/`

## 4. 查詢

Local search：

```bash
graphrag query --root graphrag_npu_0721 --method local "Which drugs are connected through protein interactions?"
```

Global search：

```bash
graphrag query --root graphrag_npu_0721 --method global "Summarize the major biomedical relationship patterns in this dataset."
```

Basic search：

```bash
graphrag query --root graphrag_npu_0721 --method basic "What biomedical entities are mentioned?"
```

Drift search：

```bash
graphrag query --root graphrag_npu_0721 --method drift "Find related disease and protein communities."
```

## 5. Streamlit 查詢

Streamlit 已接上 GraphRAG CLI，預設查 `graphrag_npu_0721`。

```bash
python -m streamlit run app.py
```

左側選 `GraphRAG CLI`，再選 query method。

## 6. 直接看 output

```python
import pandas as pd

entities = pd.read_parquet("graphrag_npu_0721/output/entities.parquet")
relationships = pd.read_parquet("graphrag_npu_0721/output/relationships.parquet")
communities = pd.read_parquet("graphrag_npu_0721/output/communities.parquet")
reports = pd.read_parquet("graphrag_npu_0721/output/community_reports.parquet")
```

## 7. Community 演算法

GraphRAG 會先用 LLM 抽取 entities / relationships，建立 entity graph。接著在 graph 上做 Leiden community detection，產生 communities，再用 LLM 生成 community reports。

設定位置：

```yaml
cluster_graph:
  max_cluster_size: 10
  seed: 42
```
