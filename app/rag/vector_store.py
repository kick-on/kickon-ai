from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from pymongo import MongoClient
from datetime import datetime
import numpy as np
from tqdm import tqdm
import os
import boto3
from dotenv import load_dotenv
import posixpath

os.environ["HF_HOME"] = "./huggingface_cache"

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "kickon"
COLLECTION_NAME = "youtube_comments"
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX")

# FAISS 인덱스 저장 디렉토리
FAISS_DIR = "kickon_vector_search/faiss_index"

# 임베딩 모델 설정 (저장 시와 일치해야 함)
embedding_model = HuggingFaceEmbeddings(
    model_name="/opt/models/all-MiniLM-L6-v2"
)

def save_faiss_index(embeddings, metadatas):
    """FAISS 인덱스를 생성하고 저장 + S3 업로드"""
    docs = [Document(page_content=meta["text"], metadata=meta) for meta in metadatas]
    vectorstore = FAISS.from_documents(docs, embedding_model)
    
    os.makedirs(FAISS_DIR, exist_ok=True)
    vectorstore.save_local(FAISS_DIR)
    print("✅ 로컬에 FAISS 인덱스 저장 완료")

    upload_faiss_to_s3(FAISS_DIR, S3_BUCKET, S3_PREFIX)

def upload_faiss_to_s3(local_dir, bucket, s3_prefix):
    """로컬 디렉토리 내 모든 파일을 S3에 업로드"""
    s3 = boto3.client("s3")

    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_path = posixpath.join(s3_prefix, relative_path)

            s3.upload_file(local_path, bucket, s3_path)
            print(f"업로드 완료 → s3://{bucket}/{s3_path}")

def load_faiss_index():
    """FAISS 인덱스를 로드"""
    if not os.path.exists(FAISS_DIR):
        raise FileNotFoundError("FAISS 인덱스가 존재하지 않습니다.")
    return FAISS.load_local(FAISS_DIR, embedding_model)

def save_faiss_index_from_mongo(top_comments):
    """
    대표 댓글(top_comments)을 받아 FAISS 인덱스를 생성하고 저장.
    """

    embeddings = []
    metadata = []

    for comment in tqdm(top_comments):
        text = comment.get("text_for_embedding")
        if text:
            emb = embedding_model.embed_query(text)
            embeddings.append(emb)
            metadata.append({
                "video_id": comment["video_id"],
                "text": text,
                "query": comment.get("query", ""),
                "like_count": comment.get("like_count", 0),
                "created_at": comment.get("created_at", datetime.utcnow().isoformat())
            })

    if embeddings:
        save_faiss_index(np.array(embeddings), metadata)
        print(f"✅ 총 {len(embeddings)}개 문장 벡터 저장 완료")
    else:
        print("❌ 저장할 임베딩이 없습니다")