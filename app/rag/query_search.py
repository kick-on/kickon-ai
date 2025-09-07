from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from typing import List
import os

# Hugging Face offline mode 설정
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

try:
    embedding_model = HuggingFaceEmbeddings(model_name="/opt/models/all-MiniLM-L6-v2")
except Exception as e:
    print("❌ HuggingFaceEmbeddings 생성 실패:", str(e))
    raise

def reformulate_query(raw_topic: str) -> str:
    """
    단순한 키워드 기반 주제를 문맥이 풍부한 검색 쿼리 문장으로 변환
    """
    query_for_embedding = f"{raw_topic} 경기에서 팬들은 어떤 반응을 보였을까?"
    #query_for_embedding = f"{raw_topic} 경기에서 어떤 결정적 장면이나 반전이 있었는지 알려줘"

    return query_for_embedding

def search_comments(query: str, k: int = 5) -> List[Document]:
    """
    사용자의 질의(query)에 대해 FAISS 인덱스를 통해 관련 댓글 검색
    :param query: 사용자의 질문
    :param k: 검색 결과 개수
    :return: Document 객체 리스트
    """
    db = FAISS.load_local("kickon_vector_search/faiss_index", embedding_model, allow_dangerous_deserialization=True)

    refined_query = reformulate_query(query)  # 쿼리 재구성
    return db.similarity_search(refined_query, k=k)