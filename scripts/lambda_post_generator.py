from app.rag.gpt_generate_post import run_rag_generation
import boto3, json

sqs = boto3.client('sqs')
SQS_NEXT = "게시글 생성 후 RDS 저장용 Lambda로 보낼 큐 URL"

def lambda_handler(event, context):
    topic = json.loads(event['Records'][0]['body'])['topic']
    user, result = run_rag_generation(topic)

    sqs.send_message(
        QueueUrl=SQS_NEXT,
        MessageBody=json.dumps({
            "topic": topic,
            "user_pk": user.pk,
            "title": result['title'],
            "contents": result['contents']
        })
    )