from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from .vector_store import get_vector_store

def build_qa_chain():
    """
    Builds the RAG question-answering chain using LangChain.
    """
    vector_store = get_vector_store()
    
    # We use search_kwargs to limit the number of documents retrieved
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    
    # Use the mini model for cost efficiency
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # Define the system prompt for the QA process
    template = """You are a helpful assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know. 
Use three sentences maximum and keep the answer concise.

Context:
{context}

Question:
{question}

Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        """Helper to format documents for the prompt."""
        return "\n\n".join(doc.page_content for doc in docs)

    # Build the chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
