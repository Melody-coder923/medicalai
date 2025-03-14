import chromadb

client = chromadb.HttpClient(host='localhost', port=8000)

from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def load_medical_knowledge(file_path):
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        return loader.load()
    except Exception as e:
        return []


def create_vector_db(documents, model_name):
    try:
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        return Chroma.from_documents(documents=documents,
                                     collection_name="medical_knowledge",
                                     embedding=embeddings,
                                     client=client)
    except Exception as e:
        return None


file_path = "/home/zeus/content/medicalreport/medical_knowledge.txt"
documents = load_medical_knowledge(file_path)

# 创建向量数据库
db = create_vector_db(documents,
                      model_name="sentence-transformers/all-MiniLM-L6-v2")

medical_knowledge_collection = client.get_collection(name="medical_knowledge")
results = medical_knowledge_collection.query(
    query_texts=["This is a query document about rocket"
                 ],  # Chroma will embed this for you
    n_results=2  # how many results to return
)
print(results)
