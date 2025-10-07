import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# ✅ Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file")

# 1. Reload FAISS store
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
vectorstore = FAISS.load_local("faiss_store", embeddings, allow_dangerous_deserialization=True)

# 2. Ask a test query
query = "What are customers saying about the product?"
results = vectorstore.similarity_search(query, k=2)

# 3. Print results
print(f"🔎 Query: {query}\n")
for i, doc in enumerate(results, start=1):
    print(f"Result {i}: {doc.page_content}\n")