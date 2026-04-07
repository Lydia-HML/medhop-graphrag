import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables (OPENAI_API_KEY)
load_dotenv()

from src.document_loader import load_and_split_document
from src.vector_store import add_documents_to_db, get_vector_store
from src.rag_chain import build_qa_chain

st.set_page_config(page_title="RAG Application", page_icon="📝", layout="centered")

st.title("📝 智慧文件問答系統 (RAG)")
st.caption("基於 LangChain + Streamlit + ChromaDB 打造的本地 AI 小幫手")

# Sidebar for configuration and upload
with st.sidebar:
    st.header("1. API 設定")
    api_key = st.text_input("輸入您的 OpenAI API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        
    st.divider()
    
    st.header("2. 上傳文件")
    uploaded_file = st.file_uploader("請上傳 PDF 或 TXT 檔", type=("txt", "pdf"))
    
    if st.button("處理文件"):
        if not uploaded_file:
            st.warning("請先上傳文件！")
        elif not os.environ.get("OPENAI_API_KEY"):
            st.error("請確認已輸入 OpenAI API Key 或寫入 .env 中！")
        else:
            with st.spinner("文件處理中 (切割與轉換向量)..."):
                try:
                    # 1. Load and split
                    chunks = load_and_split_document(uploaded_file)
                    st.info(f"文件切割完成！共分為 {len(chunks)} 個段落。")
                    
                    # 2. Add to Vector DB
                    add_documents_to_db(chunks)
                    st.success("文件已成功存入向量資料庫！")
                except Exception as e:
                    st.error(f"發生錯誤: {e}")

st.header("3. 對文件提問")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("請輸入您想問文件中關於什麼的問題？"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("抱歉，我需要 OpenAI API Key 才能回答問題！請於左側輸入。")
    else:
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    # Initialize QA Chain
                    qa_chain = build_qa_chain()
                    # Execute RAG query
                    response = qa_chain.invoke(prompt)
                    st.markdown(response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"回答時發生錯誤：{e}")
