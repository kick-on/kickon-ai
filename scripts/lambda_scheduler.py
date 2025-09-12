import json
import boto3
from app.scheduler.post_generation_scheduler import setup_game_day_jobs
from app.db.sql.session import SessionLocal
import os

sqs = boto3.client("sqs")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")  # SQS URL 환경변수

def lambda_handler(event, context):
    db = SessionLocal()
    sqs_jobs = setup_game_day_jobs(db)  # 오늘 경기 기반 SQS 전송용 job 생성

    if not sqs_jobs:
        print("오늘 경기 기반 job 없음")
        return {"statusCode": 200, "body": "No jobs to send"}

    # SQS로 전송
    for job in sqs_jobs:
        response = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(job)
        )
        print(f"📩 Sent to SQS: {job}")

    return {"statusCode": 200, "body": f"Sent {len(sqs_jobs)} jobs to SQS"}