# 《MedHop GraphRAG: Building a Biomedical Multi-hop Question Answering System》V1.0

這是一個使用 **Python, LangChain, Streamlit, ChromaDB 與 OpenAI** 撰寫的本地端文件問答系統。它可以讀取 PDF 與文字檔入庫，透過向量檢索尋找相關內容，再交給 LLM 總結成自然流暢的回答。

## 系統需求
- Python 3.9 以上
- OpenAI API Key

## 快速開始

1. **建立虛擬環境 (建議)：**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **安裝所需套件：**
   ```bash
   pip install -r requirements.txt
   ```

3. **設定環境變數：**
   你可以複製 `.env.example` 並更名為 `.env`，填上 `OPENAI_API_KEY`：
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   *註：也可以在網頁啟動後，直接從左側設定列輸入 API Key*

4. **啟動應用程式：**
   ```bash
   python -m streamlit run app.py
   ```
   它將會在瀏覽器開啟對應的網頁 (預設為 http://localhost:8501)

## 目錄結構
- `app.py`: Streamlit 主應用程式進入點。
- `src/document_loader.py`: 負責將上傳的文件 (PDF/TXT) 載入並切分為小段落 (chunks)。
- `src/vector_store.py`: 負責初始化 ChromaDB 並使用 OpenAI Embeddings 把切段後的文字轉為向量存起來。
- `src/rag_chain.py`: LangChain Retrieval QA Chain，將檢索到的資料送到 `gpt-4o-mini` 模型取得回答。
- `requirements.txt`: 專案相依套件清單。
- `.env.example`: 環境變數範例檔。
