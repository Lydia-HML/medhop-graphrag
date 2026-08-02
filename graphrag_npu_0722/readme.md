# graphrag_npu_0722

這是本專案主要使用的 Microsoft GraphRAG root。完整上手教學請先閱讀根目錄的 `README.md`。

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
| `input/` | MedHop input text。 |
| `prompts/` | GraphRAG prompt templates。 |
| `output/` | GraphRAG indexed artifacts。 |
| `evaluate_medhop.py` | MedHop 評估腳本。 |
| `GRAPHRAG_NPU_0722_EXPERIMENT.md` | 實驗紀錄。 |

## 本機 API

此 root 預設使用本機 OpenAI-compatible API：

```text
http://127.0.0.1:13305/api/v1
```
