# graphrag_npu_0722

這是本專案主要使用的 Microsoft GraphRAG root。完整上手教學請先閱讀根目錄的 `README.md`。

MedHop 資料、`input/` 文件與 `output/` indexing artifacts 都不隨
repository 散布。請從專案根目錄執行 `python scripts/download_medhop.py`
及 `python scripts/prepare_medhop.py`，再建立本機 index。

## 教材資源

- 教學簡報：[AMD AIPC MedHop GraphRAG](https://gamma.app/docs/AMD-AIPC-MedHop-GraphRAG--ck9fdgg1feyy6u1?mode=doc)
- Demo 影片：[YouTube Demo](https://youtu.be/n04f6Txv7yU)

## 架構圖

![MedHop GraphRAG 架構圖](../assets/architecture-graphrag.svg)

## 常用指令

從專案根目錄執行：

```powershell
graphrag index --root graphrag_npu_0722
graphrag query --root graphrag_npu_0722 --method local "your question"
```

## 主要內容

| 路徑 | 說明 |
|---|---|
| `settings.yaml` | GraphRAG CLI 設定檔。 |
| `input/` | 本機準備的 MedHop input text；不提交至 Git。 |
| `prompts/` | GraphRAG prompt templates。 |
| `output/` | 本機 GraphRAG indexed artifacts；不提交至 Git。 |
| `evaluate_medhop.py` | MedHop 評估腳本。 |
| `GRAPHRAG_NPU_0722_EXPERIMENT.md` | 實驗紀錄。 |

## 本機 API

此 root 預設使用本機 OpenAI-compatible API：

```text
http://127.0.0.1:13305/api/v1
```
