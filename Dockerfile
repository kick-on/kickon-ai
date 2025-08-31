# AWS Lambda Python 3.9 베이스 이미지
FROM public.ecr.aws/lambda/python:3.9

# 시스템 패키지 설치 (Rust + build-essential)
RUN yum install -y gcc gcc-c++ make curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y

# 캐시 디렉토리 및 모델 디렉토리 환경 변수
ENV HF_HOME=/root/.cache/huggingface
ENV MODEL_DIR=/models/all-MiniLM-L6-v2
ENV SENTENCE_TRANSFORMERS_HOME=$MODEL_DIR

# requirements.txt 복사 및 패키지 설치 (Rust 환경 포함)
COPY requirements.txt .
RUN /bin/bash -c "source $HOME/.cargo/env && \
    pip install --upgrade pip && \
    pip install -r requirements.txt"

# HuggingFace 모델 미리 다운로드
RUN /bin/bash -c "source $HOME/.cargo/env && \
    python3 -c 'from huggingface_hub import snapshot_download; snapshot_download(\"sentence-transformers/all-MiniLM-L6-v2\", local_dir=\"/models/all-MiniLM-L6-v2\")'"

# 나머지 코드 복사
COPY . .

# Lambda 핸들러 경로 설정
CMD ["scripts.lambda_handler.lambda_handler"]