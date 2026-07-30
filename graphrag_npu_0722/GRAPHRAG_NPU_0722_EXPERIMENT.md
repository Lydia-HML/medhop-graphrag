# GraphRAG NPU 0722 實驗：從零開始完整操作手冊

這份文件說明 `graphrag_npu_0722` 實驗的目的、環境、資料流、Notebook 每個儲存格、GraphRAG 索引流程、輸出檔案、驗證方式與常見錯誤。內容以完全沒有 Python、Jupyter、LLM 或 GraphRAG 基礎的使用者為對象。

> 實際 Notebook 名稱是 `medhop_graphrag.ipynb`，不是 `medhop_graph.ipynb`。本文件以下均以實際檔名為準。

## 1. 這個實驗在做什麼？

本實驗把 MedHop 生醫多跳問答資料轉成純文字，交給 Microsoft GraphRAG 建立知識圖譜。文字生成模型和向量模型都透過本機 Lemonade FastFlowLM 的 OpenAI-compatible API 執行，主要運算裝置為 NPU。

整體流程如下：

```text
Hugging Face 的 MedHop 資料集
        ↓
選取 train split 前 20 筆資料
        ↓
轉成 20 個 UTF-8 純文字檔
        ↓
切成有重疊的文字片段（text units）
        ↓
Qwen3 4B 擷取生醫實體與關係
        ↓
建立圖譜、社群及社群摘要
        ↓
Embed-Gemma 300M 建立向量索引
        ↓
輸出 Parquet、GraphML、LanceDB、統計與日誌
```

### 核心名詞

- **LLM**：大型語言模型。本實驗用 Qwen3 4B 找實體、關係與撰寫摘要。
- **Embedding**：把文字轉成數字向量，讓系統能以語意相似度搜尋。本實驗使用 Embed-Gemma 300M。
- **實體（entity）**：例如藥物、基因、蛋白質、疾病。
- **關係（relationship）**：例如「藥物 A 治療疾病 B」或「蛋白質 X 與蛋白質 Y 互作」。
- **知識圖譜**：以節點表示實體，以邊表示關係的資料結構。
- **社群（community）**：圖譜中彼此關聯緊密的一群節點。
- **RAG**：回答問題前先檢索相關資料，再讓模型依資料回答。
- **GraphRAG**：除了文字檢索，也利用圖譜、實體、關係及社群摘要回答問題。

## 2. 專案內的重要檔案

| 路徑 | 用途 |
|---|---|
| `medhop_graphrag.ipynb` | 下載 MedHop、檢查資料、格式化並產生 20 個輸入檔 |
| `settings.yaml` | GraphRAG 模型、API、切片、圖譜、社群、向量庫與查詢設定 |
| `.env` | 儲存 `GRAPHRAG_API_KEY`；不可提交真實密鑰到公開儲存庫 |
| `run_graphrag.py` | 修正 Windows CA/SSL 問題後呼叫 GraphRAG CLI |
| `prompts/` | 實體擷取、關係擷取、社群報告及各種查詢模式使用的提示詞 |
| `input/` | Notebook 產生的 `doc_0000.txt` 至 `doc_0019.txt` |
| `output/` | 0722 當次完成實驗的主要輸出 |
| `logs/` | 0722 當次執行日誌與模型呼叫統計 |
| `cache/` | 0722 當次 LLM 快取，可減少重跑成本與時間 |
| `output/`、`logs/`、`cache/` | 依目前 `settings.yaml` 重新執行時使用的新路徑 |
| `medhop_tools.py` | 其他問答、評估與 Neo4j 輔助函式；不屬於本次標準 indexing 必要流程 |
| `utils_1.py` | OpenAI、Neo4j、token 等輔助函式；不屬於本次標準 indexing 必要流程 |

> 注意：0722 的結果保存在名稱含 `batch10_stable` 的資料夾；目前設定檔則指向一般的 `output`、`logs`、`cache`。重新執行後請到目前設定的路徑找結果，不要誤以為程式沒有輸出。

## 3. 執行前準備

### 3.1 硬體與軟體

需要：

1. Windows 電腦及可用的 NPU 執行環境。
2. Lemonade/FastFlowLM 已啟動，API 位址為 `http://127.0.0.1:13305/api/v1`。
3. 本機已有以下模型註冊名稱：
   - `qwen3-it-4b-FLM`
   - `embed-gemma-300m-FLM`
4. Miniforge 或 Anaconda。
5. Jupyter Notebook 或 VS Code 的 Jupyter 擴充套件。

### 3.2 建立 Python 環境

在 Miniforge Prompt 或 PowerShell 執行：

```powershell
conda create -n graphrag python=3.11 -y
conda activate graphrag
conda install -c conda-forge python-dateutil -y
python -m pip install --upgrade pip
python -m pip install graphrag==3.0.9
python -m pip install pandas tiktoken datasets python-dotenv openai certifi jupyter
```

每次開啟新的終端機後，都要先執行：

```powershell
conda activate graphrag
```

### 3.3 確認安裝成功

```powershell
python --version
python -m pip show graphrag
python -c "import tiktoken; print('tiktoken OK')"
graphrag --help
```

若 `graphrag --help` 顯示說明文字，代表 CLI 已安裝。

### 3.4 設定 API Key

`.env` 至少需要：

```dotenv
GRAPHRAG_API_KEY=lemonade
```

此實驗連的是本機服務，`lemonade` 是 API SDK 所需的占位值。若日後改連外部服務，請換成真正密鑰，並確保 `.env` 已列入 `.gitignore`。

### 3.5 測試 Lemonade API

先開啟一個 PowerShell，找出 `flm.exe` 並檢查模型：

```powershell
$flm = Get-ChildItem -LiteralPath "$env:USERPROFILE\.cache\lemonade\bin\flm\npu" `
  -Recurse -Filter flm.exe -File |
  Select-Object -First 1 -ExpandProperty FullName

& $flm check qwen3-it:4b
& $flm check embed-gemma:300m
```

接著啟動本機模型服務；這個視窗在實驗期間必須保持開啟：

```powershell
& $flm serve qwen3-it:4b --embed 1 --host 127.0.0.1 --port 13305 --ctx-len 8192
```

再開第二個 PowerShell 測試 API 是否可連線：

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:13305/api/v1/models' -TimeoutSec 20 |
  ConvertTo-Json -Depth 5
```

輸出中應能看到 `qwen3-it-4b-FLM` 和 `embed-gemma-300m-FLM`。實際的 FLM 模型別名可能因安裝版本不同；若 `check` 或 `serve` 顯示找不到模型，先用 `& $flm list --filter installed --json` 查看已安裝名稱，再把指令中的別名替換成實際名稱。API 測試成功後才執行 Notebook 的 Cell 3。若發生 `Connection refused`，通常不是 Python 程式錯，而是本機 API 尚未啟動或連接埠不同。

## 4. Notebook 每個步驟詳解

Notebook 共 18 個儲存格，編號為 Cell 0 到 Cell 17。Markdown 儲存格是說明或指令，不會自動執行；Code 儲存格才是 Python 程式。

### Cell 0：建立環境的說明

內容列出建立 `graphrag` Conda 環境和安裝套件的指令。

**用途**：讓所有套件安裝在獨立環境，避免和電腦上其他 Python 專案衝突。

**新手注意**：這是 Markdown 文字，不是在 Notebook 內直接執行；請把命令貼到終端機。

### Cell 1：檢查 GraphRAG 安裝

此說明儲存格列出 `pip show`、匯入 `tiktoken` 與 `graphrag --help`。

**用途**：在下載資料或跑數小時實驗之前，先發現套件或 CLI 安裝問題。

### Cell 2：載入 `.env`

```python
%load_ext dotenv
%dotenv C:\Users\karen\Desktop\Medhop_npu\graphrag_npu_0722\.env
```

**用途**：將 `.env` 中的 `GRAPHRAG_API_KEY` 放入目前 Notebook 的環境變數。

**語法說明**：以 `%` 開頭的是 Jupyter magic，不是一般 Python 語法。

**換電腦時**：請把絕對路徑改成新電腦上的實際專案路徑。

### Cell 3：建立 Lemonade API 用戶端

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:13305/api/v1",
    api_key="lemonade",
)

def chat(messages, model="qwen3-it-4b-FLM"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    return response.choices[0].message.content
```

**用途**：用 OpenAI Python SDK 呼叫本機 Lemonade，而非 OpenAI 雲端服務。

**重要參數**：

- `base_url`：本機 API 位址。
- `api_key`：本機服務的占位密鑰。
- `model`：Lemonade 中註冊的模型名稱。
- `temperature=0`：降低隨機性，使輸出較穩定。

`chat()` 是方便手動測試模型的函式；GraphRAG 正式 indexing 使用的是 `settings.yaml`，不是這個函式。

### Cell 4：在目前 Kernel 安裝 datasets

```python
import sys
!{sys.executable} -m pip install datasets
```

**用途**：確保 `datasets` 安裝到 Notebook 正在使用的 Python，而不是另一個 Python 環境。

**新手注意**：第一次會下載及安裝套件；已安裝時可略過。`!` 表示從 Notebook 執行終端機命令。

### Cell 5：修正 Windows SSL 憑證

```python
import ssl
import certifi

_original_create_default_context = ssl.create_default_context

def create_certifi_context(*args, **kwargs):
    kwargs.pop("cafile", None)
    kwargs.pop("capath", None)
    kwargs.pop("cadata", None)
    return _original_create_default_context(
        *args,
        cafile=certifi.where(),
        **kwargs,
    )

ssl.create_default_context = create_certifi_context
```

**用途**：讓 HTTPS 下載使用 `certifi` 提供的 CA 憑證，避開某些 Windows 憑證庫損壞或格式問題。

**影響範圍**：只影響目前 Notebook Kernel。`run_graphrag.py` 另有相同目的的修正，供 CLI indexing 使用。

### Cell 6：下載 MedHop 資料集

```python
from datasets import load_dataset

ds = load_dataset("bigbio/medhop", "medhop_source")
print(ds)
print(ds["train"][0])
print(f"Train size: {len(ds['train'])}")
```

**用途**：從 Hugging Face 載入 MedHop 的原始來源格式，並查看資料集分割、第一筆內容與 train 筆數。

**資料欄位**：

- `id`：題目識別碼。
- `query`：問題。
- `candidates`：候選答案。
- `supports`：回答所需的多篇支持文件。
- `answer`：標準答案。

第一次執行需要網路並會下載資料；之後通常使用本機快取。

### Cell 7：檢查單筆資料結構

```python
item = ds["train"][0]

print(type(item))
print(item.keys() if hasattr(item, "keys") else item)
print("ID:", item["id"])
print("Question:", item["query"])
print("Answer:", item["answer"])
print("Candidates:", item["candidates"])
print("supports type:", type(item["supports"]))
print("Support count:", len(item["supports"]))
print("First support:", item["supports"][0])
```

**用途**：確認資料型別與欄位都符合預期，避免格式化時因欄位不存在而失敗。

### Cell 8：將不同型別的支持文件轉成文字

```python
def support_to_text(support):
    if isinstance(support, str):
        return support
    if isinstance(support, (list, tuple)):
        return "\n".join(map(str, support))
    if isinstance(support, dict):
        title = support.get("title", "")
        text = support.get("text", support.get("content", ""))
        return f"{title}\n{text}".strip()
    return str(support)

documents = [support_to_text(support) for support in item["supports"]]
context = "\n\n".join(documents)
print(context[:2000])
```

**用途**：建立能處理字串、list、tuple 或 dict 的通用轉換器，最後將所有支持文件合併成 `context`。

**為何要做**：不同資料集或版本的 `supports` 可能不是相同型別；先正規化可降低程式因資料格式改變而中斷的機率。

### Cell 9：第一版 MedHop 文字格式化函式

此 Cell 定義 `medhop_item_to_text(item, include_answer=True)`，把一筆資料排成：

```python
def medhop_item_to_text(item, include_answer=True):
    candidates_text = "\n".join(
        f"{i + 1}. {candidate}"
        for i, candidate in enumerate(item["candidates"])
    )

    supports_text = "\n\n".join(
        f"[Supporting Document {i + 1}]\n{support}"
        for i, support in enumerate(item["supports"])
    )

    answer_text = (
        f"\n\nGold Answer:\n{item['answer']}"
        if include_answer
        else ""
    )

    return f"""ID:
{item["id"]}

Question:
{item["query"]}

Candidate Answers:
{candidates_text}

Supporting Documents:
{supports_text}{answer_text}
""".strip()
```

```text
ID
Question
Candidate Answers
Supporting Documents
Gold Answer
```

**用途**：把結構化欄位轉成 GraphRAG 能讀取的純文字。

**重要風險**：預設包含 `Gold Answer`，適合人工檢查，但若用來評估問答準確率會造成答案洩漏。

### Cell 10：預覽第一版格式化結果

```python
item = ds["train"][0]
text = medhop_item_to_text(item)
print(text[:5000])
```

**用途**：只預覽前 5,000 個字元，檢查標題、候選答案、支持文件和答案是否排列正確，不會寫入檔案。

### Cell 11：資料準備階段的分隔說明

這是 Markdown 標題，用來提示接下來要正式建立 GraphRAG 的 `input/`。

### Cell 12：設定專案與輸入路徑

```python
from pathlib import Path

PROJECT_ROOT = Path(
    r"C:\Users\karen\Desktop\Medhop_npu\graphrag_npu_0722"
)
INPUT_DIR = PROJECT_ROOT / "input"
INPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Project:", PROJECT_ROOT)
print("Input:", INPUT_DIR)
```

**用途**：定義專案根目錄，並在不存在時建立 `input/`。

**語法說明**：字串前的 `r` 表示 raw string，避免 Windows 路徑中的反斜線被解讀成跳脫字元。

### Cell 13：正式版格式化函式，預設不含答案

Cell 13 重新定義同名的 `medhop_item_to_text()`，把 `include_answer` 預設改成 `False`。

```python
def medhop_item_to_text(item, include_answer=False):
    candidates_text = "\n".join(
        f"{i + 1}. {candidate}"
        for i, candidate in enumerate(item["candidates"])
    )

    supports_text = "\n\n".join(
        f"[Supporting Document {i + 1}]\n{support}"
        for i, support in enumerate(item["supports"])
    )

    parts = [
        f"ID:\n{item['id']}",
        f"Question:\n{item['query']}",
        f"Candidate Answers:\n{candidates_text}",
        f"Supporting Documents:\n{supports_text}",
    ]

    if include_answer:
        parts.append(f"Gold Answer:\n{item['answer']}")

    return "\n\n".join(parts)
```

**用途**：產生正式索引資料時不加入標準答案，降低答案洩漏風險。

**Python 行為**：同名函式再次定義後，新的版本會取代 Cell 9 的版本。因此 Notebook 應由上到下依序執行。

### Cell 14：清除舊輸入並產生 20 個文件

```python
SMOKE_TEST_SIZE = 20

for old_file in INPUT_DIR.glob("doc_*.txt"):
    old_file.unlink()

for index, item in enumerate(ds["train"].select(range(SMOKE_TEST_SIZE))):
    text = medhop_item_to_text(item, include_answer=False)
    output_file = INPUT_DIR / f"doc_{index:04d}.txt"
    output_file.write_text(text, encoding="utf-8")

generated_files = sorted(INPUT_DIR.glob("*.txt"))
print("Generated:", len(generated_files))
for file in generated_files:
    print(file.name, file.stat().st_size, "bytes")
```

**用途**：

1. 刪除先前的 `doc_*.txt`。
2. 選取 train split 前 20 筆。
3. 以不含答案的格式輸出 UTF-8 檔案。
4. 顯示檔名與大小，確認共產生 20 份文件。

**重要警告**：這個 Cell 會刪除 `input/` 內所有符合 `doc_*.txt` 的舊檔。若其中有手動整理的重要內容，請先備份。

`SMOKE_TEST_SIZE` 可改成其他數量，但資料越多，索引時間、模型呼叫次數與儲存空間都會增加。

### Cell 15：人工檢查輸入檔

```python
sample_file = sorted(INPUT_DIR.glob("*.txt"))[0]
print(sample_file)
print(sample_file.read_text(encoding="utf-8")[:3000])
```

**用途**：讀取第一份輸入文件的前 3,000 個字元，確認 UTF-8 顯示正常、欄位完整且沒有 Gold Answer。

### Cell 16：初始化 GraphRAG 專案的說明

```powershell
graphrag init --root C:\Users\karen\Desktop\Medhop_npu\graphrag_npu_0722
```

**用途**：建立預設 `settings.yaml`、`.env` 與 `prompts/`。

**本專案注意事項**：這些檔案已存在。不要任意再次執行 `init` 覆蓋已調整好的 NPU 設定與生醫提示詞。Cell 中曾出現查看 `graphrag_npu_0721` 的命令，那只是舊專案檢查，不是 0722 實驗的必要步驟。

### Cell 17：執行 GraphRAG indexing 的說明

一般命令為：

```powershell
graphrag index --root ./graphrag_npu_0722 --verbose
```

本機若有 Windows SSL 問題，建議使用專案包裝腳本：

```powershell
conda activate graphrag
cd C:\Users\karen\Desktop\Medhop_npu\graphrag_npu_0722
python .\run_graphrag.py index --root . --method standard --verbose
```

**用途**：正式啟動 GraphRAG 標準索引流程。這是耗時最久的步驟。

## 5. `settings.yaml` 每組設定的用途

### 5.1 同時請求數

```yaml
concurrent_requests: 1
```

一次只讓一個文字生成請求進入 NPU。本實驗優先求穩定，不追求最高吞吐量。

### 5.2 文字生成模型

- 模型：`qwen3-it-4b-FLM`
- API：`http://127.0.0.1:13305/api/v1`
- `temperature: 0`：提高可重現性。
- `timeout: 300`：單次最長等候 300 秒。
- 最多重試 2 次，延遲 5 到 10 秒。
- 每 5 秒最多送出 1 個請求。

用途是擷取圖譜、合併實體描述、建立社群摘要及執行查詢。

### 5.3 Embedding 模型

- 模型：`embed-gemma-300m-FLM`
- 最多重試 3 次。
- 每秒最多 8 個請求。
- 每批 8 段文字，最多 6,000 tokens。
- 向量維度為 768。

會建立三個 LanceDB 索引：

1. `text_unit_text`：原始文字片段。
2. `entity_description`：實體描述。
3. `community_full_content`：社群報告全文。

### 5.4 文字切片

```yaml
chunking:
  type: tokens
  size: 450
  overlap: 60
  encoding_model: cl100k_base
```

每片最多約 450 tokens，相鄰片段重疊 60 tokens。重疊可避免重要句子恰好在切割邊界被拆散。

### 5.5 圖譜擷取

實體類型包含生醫實體、基因、蛋白質、疾病、藥物、化學物、變異、表型、生物標記、路徑、生物過程與生物體。

- `max_gleanings: 0`：不追加第二輪補抓，以減少 NPU 時間。
- 實體描述摘要最長 250。
- claims extraction 關閉，所以 covariates 階段幾乎不耗時。

### 5.6 社群與社群報告

- `max_cluster_size: 10`：限制單一社群大小，避免提示詞過長。
- `seed: 42`：固定隨機種子，增加重現性。
- 報告最長 600。
- 報告輸入上限 4,000。

這一階段是本次錯誤主要來源：部分輸出達到模型長度上限，或 JSON 在結尾前被截斷。

### 5.7 輸出與快取

目前設定為：

```yaml
input_storage:  input/
output_storage: output/
reporting:      logs/
cache:          cache/
vector_store:   output/lancedb/
```

快取可讓重跑時重用相同請求結果。若更換模型、提示詞或輸入資料，舊快取可能不再適用，應以新的資料夾保留不同實驗版本。

### 5.8 查詢模式

- **Local Search**：從特定實體、關係及文字片段回答細節問題。
- **Global Search**：以社群報告 map/reduce 回答整體趨勢問題。
- **DRIFT Search**：結合全域線索與逐步局部探索。
- **Basic Search**：一般向量 RAG。

Local 與 Global 的 context 上限設成 2,400 tokens，因為預設 12,000 在此模型與環境中可能產生空回應或超長錯誤。

## 6. GraphRAG indexing 的 10 個工作流程

| 順序 | Workflow | 用途 | 本次耗時（秒） |
|---:|---|---|---:|
| 1 | `load_input_documents` | 讀入 20 個 UTF-8 文件 | 1.13 |
| 2 | `create_base_text_units` | 依 450/60 token 規則切片 | 3.18 |
| 3 | `create_final_documents` | 建立文件與文字片段的對照 | 0.26 |
| 4 | `extract_graph` | 用 Qwen3 擷取實體、關係並整理描述 | 47,763.26 |
| 5 | `finalize_graph` | 整理、合併並輸出最終圖譜 | 4.40 |
| 6 | `extract_covariates` | 建立 claims/covariates；本實驗關閉 claims | 0.004 |
| 7 | `create_communities` | 將關聯緊密節點分群 | 1.98 |
| 8 | `create_final_text_units` | 將文字片段連回實體與關係 | 2.05 |
| 9 | `create_community_reports` | 用 Qwen3 為各社群撰寫摘要 | 23,964.89 |
| 10 | `generate_text_embeddings` | 用 Embed-Gemma 建立 LanceDB 向量 | 2,824.66 |

總執行時間為 74,567.03 秒，約 20 小時 43 分鐘。最耗時的是圖譜擷取，其次是社群報告。

## 7. 輸出檔案怎麼看？

| 檔案 | 內容與用途 |
|---|---|
| `documents.parquet` | 原始文件與識別資訊 |
| `text_units.parquet` | 切片後的文字、token 數及圖譜連結 |
| `raw_entities.parquet` | LLM 原始擷取的實體 |
| `raw_relationships.parquet` | LLM 原始擷取的關係 |
| `entities.parquet` | 合併與整理後的最終實體 |
| `relationships.parquet` | 整理後的最終關係 |
| `communities.parquet` | 社群階層、成員及關係 |
| `community_reports.parquet` | 社群標題、摘要、全文與 findings |
| `graph.graphml` | 可用 Gephi、Cytoscape 或 NetworkX 開啟的圖譜 |
| `lancedb/` | GraphRAG 查詢使用的向量資料庫 |
| `stats.json` | 文件數、總時間及每個 workflow 的耗時與記憶體 |
| `context.json` | 額外的執行 context；本次內容為空物件不代表索引失敗 |

本次日誌顯示向量資料約包含：

- `text_unit_text`：690 rows
- `entity_description`：2,360 rows
- `community_full_content`：353 rows

> 上述為日誌所記錄的向量寫入筆數；它們分別是文字片段、實體描述與社群全文的向量，不等同於原始文件數。原始文件仍是 20 份。

### 7.1 索引完成後如何查詢

查詢前必須同時滿足三個條件：Lemonade API 仍在執行、Conda 的 `graphrag` 環境已啟用、`settings.yaml` 指向實際索引所在的 output 與 LanceDB。0722 歷史成果位於 `output_batch10_stable/`，而目前設定指向 `output/`；若要查詢歷史成果，請先複製設定檔並將 `output_storage.base_dir` 與 `vector_store.db_uri` 改成歷史路徑，避免不小心混用兩批索引。

在專案目錄執行 Local Search：

```powershell
conda activate graphrag
cd C:\Users\karen\Desktop\Medhop_npu\graphrag_npu_0722
python .\run_graphrag.py query --root . --method local "Which candidate interacts with DB00773?"
```

各參數用途：

- `python .\run_graphrag.py`：使用專案的 SSL 相容入口啟動 GraphRAG。
- `query`：要求 GraphRAG 查詢既有索引，而不是重新建立索引。
- `--root .`：以目前資料夾為專案根目錄，從這裡讀取設定、輸出與向量庫。
- `--method local`：以相關實體、關係及文字片段回答具體問題。
- 最後的引號文字：使用者真正要問的問題；PowerShell 中建議用引號包住完整問題。

其他查詢模式範例：

```powershell
# 從社群報告歸納整份資料的主要主題；適合全局問題
python .\run_graphrag.py query --root . --method global "What are the main biomedical themes in this corpus?"

# 由全局線索開始，再逐步探索局部關係
python .\run_graphrag.py query --root . --method drift "How are the major drug-protein relationships connected?"

# 一般向量檢索後生成答案，不特別使用完整圖譜推理流程
python .\run_graphrag.py query --root . --method basic "Which candidate interacts with DB00773?"
```

新手應先使用 `local` 測試一個具體問題。若命令能執行但回答為空，先確認查詢讀到正確的 output，再檢查日誌是否出現 context 過長或模型輸出長度錯誤。回答能產生也不代表答案正確；MedHop 的正式準確率仍必須和保留在資料集中的 Gold Answer 另外比對。

## 8. 如何判斷實驗成功？

在專案資料夾執行：

```powershell
Get-Content .\logs_batch10_stable\indexing-engine.log -Tail 100
Select-String -Path .\logs_batch10_stable\indexing-engine.log `
  -Pattern 'ERROR|WARNING|Indexing pipeline complete'
Get-Content .\output_batch10_stable\stats.json
```

本次結果：

- 20 份文件已讀取。
- 10 個 workflow 最後皆記錄完成。
- 日誌結尾有 `Indexing pipeline complete.`。
- Embedding 428/428 成功，失敗率 0%。
- Qwen3 共嘗試 2,388 次回應，成功 2,289 次、失敗 99 次，失敗率約 4.15%。
- Parquet、GraphML、LanceDB 與統計檔均已產生。

因此結論是：**端到端 indexing 成功，但不是零錯誤的完整成功**。部分社群報告可能缺漏或品質較差。

### 這不等於問答準確率已驗證

本實驗完成的是「建立索引」。Notebook 沒有執行所有問題、解析模型答案並和 MedHop Gold Answer 比對，因此不能由 `Indexing pipeline complete` 推論 QA accuracy 很高。若要評估品質，還需要另外建立問答評估程式，至少計算 exact match、包含答案比例及失敗題目清單。

## 9. 安全重跑步驟

1. 啟動 Lemonade/FastFlowLM，確認兩個模型可用。
2. 開啟 Notebook，選擇 `graphrag` Python Kernel。
3. 從 Cell 2 開始依序執行到 Cell 15。
4. 確認畫面顯示 `Generated: 20`。
5. 開啟一份 `input/doc_*.txt`，確認不是空檔且沒有 `Gold Answer`。
6. 關閉 Notebook 或保持開啟皆可，在終端機執行 indexing。

```powershell
conda activate graphrag
cd C:\Users\karen\Desktop\Medhop_npu\graphrag_npu_0722
python .\run_graphrag.py index --root . --method standard --verbose
```

7. 等日誌出現 `Indexing pipeline complete.`。
8. 到 `settings.yaml` 指定的 `output/` 和 `logs/` 檢查新結果。

### 建議的版本保存方式

不要直接覆蓋成功實驗。每次改模型、提示詞或參數時，將下列路徑改成新的實驗名稱：

```yaml
output_storage:
  base_dir: output_實驗名稱
reporting:
  base_dir: logs_實驗名稱
cache:
  storage:
    base_dir: cache_實驗名稱
vector_store:
  db_uri: output_實驗名稱/lancedb
```

並記錄日期、模型版本、資料筆數、設定檔副本與最後 metrics，才能公平比較不同實驗。

## 10. 常見問題與解法

### `Connection refused` 或無法連到 127.0.0.1:13305

原因通常是 Lemonade 未啟動、API 連接埠不同，或模型服務正在載入。先確認服務，再測試 Cell 3。

### 找不到模型

檢查 Lemonade 內的名稱是否和 `qwen3-it-4b-FLM`、`embed-gemma-300m-FLM` 完全一致；大小寫和連字號都必須相同。

### `SSL`、`CERTIFICATE_VERIFY_FAILED`

先安裝 `certifi`，Notebook 依序執行 Cell 5；CLI 則使用 `run_graphrag.py`。

### `JSONSchemaValidationError` 或 `JSONDecodeError`

模型輸出的 JSON 被截斷或格式不符。可縮短 prompt、降低社群大小或報告輸入長度、提高模型可用輸出長度，並保留 retry。不要只看最後 pipeline 是否完成，也要檢查失敗率與社群報告空值。

### `Max length reached!`

輸入加輸出超過模型限制。優先降低：

1. `community_reports.max_input_length`
2. `community_reports.max_length`
3. `cluster_graph.max_cluster_size`
4. 查詢用 `max_context_tokens`

### 執行很慢

這是預期現象。本次 20 筆資料約花 20 小時 43 分。`concurrent_requests: 1` 是為了 NPU 穩定性；提高並行數可能加速，也可能造成服務失敗或記憶體不足，應一次只調一個參數並以小資料測試。

### Notebook 顯示找不到 `datasets`

代表套件可能裝到另一個 Python。執行 Cell 4，或確認右上角 Kernel 是 `graphrag` 環境。

### 重新執行後找不到 `output_batch10_stable`

目前設定的新輸出是 `output/`。0722 歷史結果才在 `output_batch10_stable/`。永遠以當次 `settings.yaml` 的 `base_dir` 為準。

### GraphRAG 完成但回答品質不好

完成代表資料管線可運作，不代表抽取和回答一定正確。請抽查實體、關係與社群報告，並建立 MedHop Gold Answer 評估。尤其本次有 99 次 Qwen3 失敗，需要先找出受影響的社群或文件。

## 11. 新手操作檢查表

執行前：

- [ ] 已啟動 Lemonade/FastFlowLM。
- [ ] 兩個模型名稱正確且已載入。
- [ ] 已 `conda activate graphrag`。
- [ ] `.env` 有 `GRAPHRAG_API_KEY`。
- [ ] Cell 3 可成功呼叫本機 API。

資料準備後：

- [ ] `input/` 恰有 20 個 `doc_*.txt`。
- [ ] 文件不是空檔。
- [ ] 文件為 UTF-8 且中文或特殊字元無亂碼。
- [ ] 正式索引文件沒有 `Gold Answer`。

索引完成後：

- [ ] 日誌有 `Indexing pipeline complete.`。
- [ ] `stats.json` 的 `num_documents` 是 20。
- [ ] 所有主要 Parquet 檔都存在。
- [ ] `graph.graphml` 存在。
- [ ] `lancedb/` 存在。
- [ ] 已記錄失敗率，而不是只看「完成」。
- [ ] 已備份設定、提示詞、日誌與結果。

## 12. 後續建議

1. 檢查 `community_reports.parquet` 是否有空白或錯誤報告。
2. 針對 99 次失敗調低社群 prompt 長度後重跑。
3. 建立 MedHop QA 評估腳本，避免把「索引成功」誤當成「答案正確」。
4. 用 Gephi 或 Cytoscape 開啟 `graph.graphml`，抽查重要藥物、基因與疾病關係。
5. 每次實驗使用獨立 output/log/cache 名稱，並保存一份設定檔快照。

## 13. 本文件依據

- `medhop_graphrag.ipynb`
- `settings.yaml`
- `run_graphrag.py`
- `logs_batch10_stable/indexing-engine.log`
- `output_batch10_stable/stats.json`
- `output_batch10_stable/` 內的索引產物
