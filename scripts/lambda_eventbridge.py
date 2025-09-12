import json
import boto3
import os
import uuid
from datetime import datetime

events = boto3.client("events")

def lambda_handler(event, context):
    # SQS 이벤트는 Records[] 로 들어옴
    rules_created = 0

    for record in event["Records"]:
        body = json.loads(record["body"])
        bot_type = body["bot_type"]
        topic = body["topic"]
        run_at = datetime.fromisoformat(body["run_at"])

        rule_name = f"{bot_type}-{uuid.uuid4().hex[:8]}"
        run_at_utc = run_at.strftime("%Y-%m-%dT%H:%M:%SZ")

        # EventBridge Rule 생성 (at() 형식)
        events.put_rule(
            Name=rule_name,
            ScheduleExpression=f"at({run_at_utc})",
            State="ENABLED"
        )

        # Lambda 타겟 ARN (환경변수로 bot별 ARN 지정)
        target_arn = os.getenv(f"{bot_type.upper()}_BOT_ARN")

        events.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    "Id": "1",
                    "Arn": target_arn,
                    "Input": json.dumps({
                        "task": "run_bot",
                        "bot_type": bot_type,
                        "topic": topic
                    })
                }
            ]
        )

        print(f"[EventBridge Rule Created] {rule_name} -> {run_at_utc}")
        rules_created += 1

    return {"status": "ok", "rules_created": rules_created}