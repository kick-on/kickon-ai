import json
import boto3
from app.crawlers.youtube_crawler import crawl_youtube_comments_by_query
from app.crawlers.fmkorea_crawler import crawl_fmkorea_board
from app.core.config import settings

sqs = boto3.client("sqs", region_name=settings.aws_region)

def send_to_sqs(doc: dict):
    sqs.send_message(
        QueueUrl=settings.sqs_queue_url,
        MessageBody=json.dumps(doc, default=str)  # datetime 같은 건 str로 직렬화
    )
    print(f"📤 SQS 전송 완료 (source={doc['source']})")


def lambda_handler(event, context):
    print("📩 Event:", event)
    
    if "Records" in event:
        body = json.loads(event["Records"][0]["body"])
    else:
        body = event

    source = body.get("source")
    query = body.get("query")

    docs = []

    if source == "youtube":
        docs = crawl_youtube_comments_by_query(query)   # return: [doc, doc, ...]
    elif source == "fmkorea":
        docs = crawl_fmkorea_board(query, page_limit=1)  # return: [doc, doc, ...]
    else:
        return {"statusCode": 400, "body": f"Unknown source: {source}"}

    for doc in docs:
        send_to_sqs(doc)

    return {"statusCode": 200, "body": f"Sent {len(docs)} docs from {source}:{query}"}