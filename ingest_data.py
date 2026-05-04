import os
import glob
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def build_vector_db():
    print("--- Starting Data Ingestion ---")
    
    # 1. Directory Safety Check
    sops_dir = "data/sops"
    if not os.path.exists(sops_dir):
        os.makedirs(sops_dir)
        print(f"Created directory: {sops_dir}")
        print(f"🛑 STOP: Please place at least one .pdf file inside the '{sops_dir}' folder and run this again.")
        return

    pdf_files = glob.glob(os.path.join(sops_dir, "*.pdf"))
    if len(pdf_files) == 0:
        print(f"🛑 STOP: No PDFs found in '{sops_dir}'. Please add your mock SOP files and try again.")
        return
        
    # 2. Load the Documents
    print(f"Found {len(pdf_files)} PDF(s). Loading documents...")
    loader = PyPDFDirectoryLoader(sops_dir)
    docs = loader.load()
    print(f"Successfully loaded {len(docs)} pages/sections.")

    # 3. Chunk the Documents
    print("Chunking documents for optimal retrieval...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    print(f"Created {len(splits)} text chunks.")

    # 4. Generate Embeddings (Free Local Hugging Face Model)
    print("Initializing embedding model (This may take a moment to download on the first run)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2") 
    
    # 5. Build and Save FAISS Vector Store
    print("Building FAISS vector database...")
    vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
    
    vectorstore.save_local("vector_store")
    print("✅ Success! Vector database built and saved locally to the 'vector_store' folder.")

if __name__ == "__main__":
    build_vector_db()