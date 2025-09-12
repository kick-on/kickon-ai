import os
import json
import boto3

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
sqs = boto3.client("sqs")

def send_sqs_message(message_body: dict):
    """단일 메시지 SQS 전송"""
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(message_body)
    )
    print(f"📩 Sent to SQS: {message_body}")
    return response

def send_sqs_messages(messages: list[dict]):
    """여러 메시지 SQS 전송"""
    for msg in messages:
        send_sqs_message(msg)