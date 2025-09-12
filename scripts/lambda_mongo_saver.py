import json
from app.db.mongo.mongo_utils import save_youtube_comment_doc, save_fmkorea_post_doc

def lambda_handler(event, context):
    print("📩 Event:", event)

    for record in event["Records"]:
        body = json.loads(record["body"])
        source = body.get("source")

        if source == "youtube":
            save_youtube_comment_doc(body)
        elif source == "fmkorea":
            save_fmkorea_post_doc(body)
        else:
            print(f"❌ Unknown source: {source}")

    return {"statusCode": 200, "body": "MongoDB 저장 완료"}