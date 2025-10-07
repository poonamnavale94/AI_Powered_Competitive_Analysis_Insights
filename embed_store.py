import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ✅ Load environment variables from .env
load_dotenv()

# 🔑 Get OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file")

# 1. Example text (later we’ll replace with scraped reviews or other data)
text = """
This is a test document about competitive analysis.
Competitors are focusing on pricing and marketing strategies.
Customers mention product quality and fast shipping as positives.
"""

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
docs = [Document(page_content=chunk) for chunk in splitter.split_text(text)]

print(f"✅ Created {len(docs)} chunks")

# 3. Convert chunks into embeddings
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = FAISS.from_documents(docs, embeddings)

# 4. Save vector DB locally
vectorstore.save_local("faiss_store")
print("🎉 Embeddings created and stored in faiss_store folder!")