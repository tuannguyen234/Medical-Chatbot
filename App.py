import streamlit as st
import streamlit as st
import sqlite3
from google import genai as genai2
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores.faiss import FAISS
# from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
from PIL import Image
import faiss
import pickle
import io
import unicodedata
load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Streamlit UI
st.title("🧠 Multi-RAG System for Medical Q&A")

# User input (text or image)
query_text = None
uploaded_image = st.file_uploader("📷 Upload an image or enter text below:", type=["jpg", "png"])

if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded Image", use_container_width=True)
    st.write(f"🔍 Extracted Text: **{query_text}**")

query_text_input = st.text_input("💬 Or enter a medical question:")
@st.cache_resource
def embedding_model():
    embeddings = HuggingFaceEmbeddings(model_name="TuanNM171284/TuanNM171284-HaLong-embedding-medical")
    return embeddings

@st.cache_resource
def get_conversational_chain_for_text():

    prompt_template = """
    Bạn là một trợ lý y tế chuyên sâu, sử dụng hệ thống Multi-RAG để tìm kiếm và truy xuất thông tin từ cơ sở dữ liệu y khoa bao gồm văn bản và hình ảnh về triệu chứng, bệnh tật, và phương pháp điều trị. Bạn chỉ dựa vào dữ liệu trong hệ thống để trả lời. Nếu không tìm thấy thông tin phù hợp, hãy trả lời rằng câu hỏi không liên quan hoặc không có trong hệ thống\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """


    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash",
                             temperature=0.3)

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain
# @st.cache_resource
def user_input(user_question):
    # embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    # embeddings = HuggingFaceEmbeddings(model_name="keepitreal/vietnamese-sbert")
    # embeddings = HuggingFaceEmbeddings(model_name="TuanNM171284/TuanNM171284-HaLong-embedding-medical")
    new_db = FAISS.load_local(r"D:\code\RAG\faiss_VN_sbert", embedding_model(), allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question,1)
    print("-------------")
    print(type(docs))
    print(docs)
    chain = get_conversational_chain_for_text()

    if user_question is not None:
        response = chain(
            {"input_documents":docs, "question": user_question}
            , return_only_outputs=True)

        st.markdown(f"**Kết quả:**\n\n{response['output_text']}")

# @st.cache_resource
def clean_path(path: str) -> str:
    return unicodedata.normalize('NFKC', path).replace('\xa0', ' ').strip()
def user_input_images(query):
    # embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    # embeddings = HuggingFaceEmbeddings(model_name="TuanNM171284/TuanNM171284-HaLong-embedding-medical")
    
    # Load FAISS index
    vector_store = FAISS.load_local(r"D:\code\RAG\faiss_index_image", embedding_model(), allow_dangerous_deserialization=True)
    
    # Get top K results
    results = vector_store.similarity_search(query)
    print(type(results[0]))
    print(results[0])
    if results:
        matched_descriptions = [r.page_content for r in results]  # Extract descriptions
        # Connect to SQLite & retrieve matching image paths
        conn = sqlite3.connect('D:\code\DOAN\image_database copy.db')
        cursor = conn.cursor()
        
        placeholders = ",".join(["?"] * len(matched_descriptions))  # Create ?,?,? for SQL query
        cursor.execute(f"SELECT image_path FROM images WHERE description IN ({placeholders})", matched_descriptions)
        
        image_paths = [row[0] for row in cursor.fetchall()]  # Fetch all results
        conn.close()

        # return image_paths if image_paths else None
        prompt_template = """
        Dựa vào câu hỏi người dùng, hãy trả lại các đường dẫn ảnh phù hợp từ danh sách dưới đây.
        - Không được trùng lặp
        - Chỉ trả lại đường dẫn, mỗi đường dẫn nằm trên 1 dòng
        - Không thêm bất kỳ thông tin mô tả nào khác
        """
        prompt = f"{prompt_template}\n\nCâu hỏi: {query}\n\nDanh sách ảnh:\n" + "\n".join(image_paths)
        client = genai2.Client(api_key="AIzaSyC60YzCQ4IndhZd2_qdVn5a1dzUzZ56kxI")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{prompt}]
    )
        # image_indexed = {str(i): p for i, p in enumerate(image_paths)}
        # indexed_prompt = "\n".join([f"{i}: {os.path.basename(p)}" for i, p in image_indexed.items()])
        list_images = [clean_path(i.strip()) for i in response.text.split('\n') if i.strip()]
        list_images = list(set(list_images))  # bỏ trùng
        # Hiển thị từng ảnh trong danh sách
        for image in list_images:
            if os.path.exists(image):
                st.image(image, caption=image, use_container_width=True)
            else:
                st.warning(f"Không có ảnh nào liên quan: {image}")
if __name__ == "__main__":
    if query_text_input != '':
        user_input(query_text_input)
        user_input_images(query_text_input)