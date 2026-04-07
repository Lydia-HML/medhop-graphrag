import tempfile
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_split_document(uploaded_file):
    """
    Loads an uploaded file (PDF or TXT) and splits it into manageable chunks.
    """
    # Create a temporary file to save the uploaded content
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tf:
        tf.write(uploaded_file.getbuffer())
        temp_file_path = tf.name

    try:
        if file_extension == ".pdf":
            loader = PyPDFLoader(temp_file_path)
        elif file_extension == ".txt":
            loader = TextLoader(temp_file_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        documents = loader.load()

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        return chunks

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
