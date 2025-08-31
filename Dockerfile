# AWS Lambda Python 3.9 베이스 이미지
FROM public.ecr.aws/lambda/python:3.9

# 시스템 패키지 설치 (Rust + build-essential)
RUN yum install -y gcc gcc-c++ make curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    echo 'source $HOME/.cargo/env' >> ~/.bashrc

# 환경 변수 설정
ENV HF_HOME=/root/.cache/huggingface
ENV MODEL_DIR=/opt/models/all-MiniLM-L6-v2
ENV SENTENCE_TRANSFORMERS_HOME=$MODEL_DIR
ENV PATH=$HOME/.cargo/bin:$PATH

# requirements.txt 복사 및 패키지 설치 (Rust 환경 포함)
COPY requirements.txt .
RUN /bin/bash -c "source $HOME/.cargo/env && \
    pip install --upgrade pip && \
    pip install -r requirements.txt"

# S3에서 모델 압축 파일 다운로드 및 압축 해제
RUN mkdir -p /opt/models && \
    curl -o /opt/model.tar.gz https://kickon-ai-bucket.s3.ap-northeast-2.amazonaws.com/models/all-MiniLM-L6-v2.tar.gz && \
    tar -xzf /opt/model.tar.gz -C /opt/models && \
    rm /opt/model.tar.gz

# 나머지 코드 복사
COPY . .

# Lambda 핸들러 경로 설정
CMD ["scripts.lambda_handler.lambda_handler"]