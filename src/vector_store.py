import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Initialize the vector store persistently
persist_directory = "./chroma_db"

def get_vector_store():
    """
    Returns an instance of the Chroma vector store.
    """
    embeddings = OpenAIEmbeddings()
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    return vector_store

def add_documents_to_db(chunks):
    """
    Adds document chunks to the database.
    """
    vector_store = get_vector_store()
    vector_store.add_documents(documents=chunks)
    return True
