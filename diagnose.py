import os
from groq import Groq
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from huggingface_hub import InferenceClient  #使用额度不够了,目前代码中用的是groq,因为免费,但如果下载到本地电脑groq也不需要了,目前连接只是为了测试模型
from langchain.sql_database import SQLDatabase
import database_utils

from langchain.chat_models import init_chat_model
model = init_chat_model("llama3-8b-8192", model_provider="groq")


from langchain_core.output_parsers import StrOutputParser
#根据message生成提示词模板
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are a professional health advisor."),
    ("user","{input}")
])
#创建字符串解析器
output_parser= StrOutputParser()
chain= prompt_template|model| output_parser
result= chain.invoke({"input":"Please review the uploaded medical report, interpret it, and then provide me with advice in response to my questions."})


#远程服务器需要费用,本地免费
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)

# 初始化 session state, session_state需要的目的是同一次用户会话 (same user session) 的多次应用运行之间被保留下来 
if 'overall_recommendations' not in st.session_state:
    st.session_state.overall_recommendations = ""


# # 加载医学知识文档
def load_medical_knowledge(file_path):
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        return loader.load()
    except Exception as e:
        st.error(f"Failed to load documents: {e}")
        return []


# 创建向量数据库
def create_vector_db(documents, model_name):
    try:
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        return Chroma.from_documents(documents=documents,
                                     collection_name="medical_knowledge",
                                     embedding=embeddings,
                                     client=client)
    except Exception as e:
        st.error(f"Failed to create vector database: {e}")
        return None


# 调用远程模型进行推理
def query_model(client, prompt):
    try:
        response = client.invoke(prompt)
        return response
    except Exception as e:
        print(f"Error during inference: {e}")
        return None


# # 主逻辑
def get_answer(query):
    # 加载医学知识文档
    file_path = "/home/zeus/content/medicalreport/medical_knowledge.txt"
    documents = load_medical_knowledge(file_path)

    # 创建向量数据库
    db = create_vector_db(documents,
                          model_name="sentence-transformers/all-MiniLM-L6-v2")
    if db is None:
        st.error("Failed to create vector database.")
        return None

    client = init_chat_model("llama3-8b-8192", model_provider="groq")
    if client is None:
        st.error("Failed to initialize Hugging Face client.")
        return None


    # 检索相关文档
    print("Query vector db")
    results = db.similarity_search(query)
    print("Finish vector db query")

    # 构建 Prompt
    context = "\n".join([doc.page_content for doc in results])
    prompt = f"请根据以下信息回答问题：\nContext:{context}\nQuestion:{query}"

    # 调用模型
    print("Send query to model and wait")
    response = query_model(client, prompt)
    return response

# Streamlit 页面
def main():
    st.title("User Page")

    # 用户信息
    col1, col2 = st.columns(2)
    with col1:
        # 允许用户上传图片
        profile_photo = st.file_uploader("Upload your profile photo",
                                         type=["jpg", "png"])
        if profile_photo:
            st.image(profile_photo, width=100)
        else:
            st.write("Please upload a profile photo.")

        # 允许用户编辑信息
        first_name = st.text_input("First Name", "Jimmy")
        age = st.text_input("Age", "")
        gender = st.text_input("Gender", "")
        height = st.text_input("Height", "")
        weight = st.text_input("Weight", "")

        col1a, col1b = st.columns(2)
        with col1a:
            if st.button("Save", key="save_button"):
                # 调用 database_utils.add_user() 函数保存用户信息到数据库
                database_utils.add_user(first_name, age, gender, height, weight, profile_photo.name if profile_photo else None)
                st.success("User information saved!")
        with col1b:
            st.button("cancel", key="cancel_user_button")

    with col2:
        if 'lab_results' not in st.session_state:
            st.session_state.lab_results = []  # 初始化为空列表

        st.button("Add New Lab Report", key="add_lab_report_button")
        uploaded_file = st.file_uploader("Choose a file",
                                         type=["pdf", "docx", "txt"])
        if uploaded_file:
            st.session_state.lab_results.append(uploaded_file.name)
            database_utils.add_lab_report(1, uploaded_file.name)
            lab_reports_from_db = database_utils.get_lab_reports_for_user(1) 
            if lab_reports_from_db:
                for i, report in enumerate(lab_reports_from_db):
                    report_id = report[0] # lab_reports 表格的 id 列
                    report_file_name = report[2] # lab_reports 表格的 report_file_name 列 (注意索引)
                    col2a, col2b = st.columns([0.8, 0.2])
                    with col2a:
                        st.write(report_file_name)
                    with col2b:
                        if st.button("x", key=f"delete_report_db_{report_id}"):
                            database_utils.delete_lab_report(report_id)
                            st.session_state.lab_results = [r[2] for r in database_utils.get_lab_reports_for_user(1)]
                            st.rerun()
        for i, result in enumerate(st.session_state.lab_results):
            col2a, col2b = st.columns([0.8, 0.2])  # Adjust widths as needed
            with col2a:
                st.write(result)
            with col2b:
                if st.button("x", key=f"delete_report_session_{i}"):
                    del st.session_state.lab_results[i]
                    
        st.markdown(
            """
            <style>
            textarea {
                height: 200px !important;
                width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
        )
        # 创建一个容器来放置问题和推荐
        with st.container():
            question = st.text_input("Question:", "")
            if st.button("Get Answer"):
                answer = get_answer(question)
                if answer is not None:
                    if type(answer.content)==str:
                        st.session_state.overall_recommendations += answer.content+ "\n"
                else:
                    st.session_state.overall_recommendations += "No answer received.\n"
            st.text_area(label="Overall Recommendations",
                        value=str(st.session_state.overall_recommendations))


# 启动！
if __name__ == "__main__":
    main()
