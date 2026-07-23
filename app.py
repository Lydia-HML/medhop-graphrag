import os

import streamlit as st
from dotenv import load_dotenv

from src.graphrag_client import GRAPHRAG_METHODS, GRAPHRAG_ROOT, run_graphrag_query


load_dotenv()

st.set_page_config(page_title="MedHop GraphRAG", page_icon="GraphRAG", layout="centered")

st.title("MedHop GraphRAG")
st.caption("固定使用 Microsoft GraphRAG root：graphrag_npu_0721")

with st.sidebar:
    st.header("GraphRAG CLI")
    st.caption("Root")
    st.code(str(GRAPHRAG_ROOT), language="text")

    graphrag_method = st.selectbox("Query method", GRAPHRAG_METHODS)
    graphrag_api_key = st.text_input(
        "GRAPHRAG_API_KEY",
        type="password",
        help="本機 Lemonade / NPU API 若不檢查 key，可以留空；程式會用 local 當預設值。",
    )
    if graphrag_api_key:
        os.environ["GRAPHRAG_API_KEY"] = graphrag_api_key

    st.info("此介面會呼叫 GraphRAG CLI 查詢既有的 graph index。")

st.header("提問")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("輸入你的問題"):
    st.chat_message("user").markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        try:
            with st.spinner("正在呼叫 GraphRAG CLI 查詢 graphrag_npu_0721..."):
                response = run_graphrag_query(
                    method=graphrag_method,
                    question=question,
                    api_key=os.environ.get("GRAPHRAG_API_KEY"),
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as exc:
            st.error(f"查詢失敗：{exc}")
