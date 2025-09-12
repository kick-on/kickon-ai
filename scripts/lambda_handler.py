import os
import boto3
from sqlalchemy.orm import Session
from app.scheduler.post_generation_scheduler import setup_game_day_jobs
from app.db.sql.session import SessionLocal
from app.bots.post_generation_bots import (
    run_pregame_bot, run_postgame_focus_bot, run_realtime_bot, run_trend_bot
)
from scripts.lambda_crawler import lambda_handler as crawler_handler
from scripts.lambda_mongo_saver import lambda_handler as mongo_saver_handler
from scripts.lambda_rds_saver import lambda_handler as rds_handler
from app.utils.sqs_utils import send_sqs_messages, send_sqs_message

# SQS 클라이언트
sqs = boto3.client("sqs")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")  # SQS URL 환경 변수로 지정

def lambda_handler(event, context):
    # 환경변수 LAMBDA_ROLE로 역할 구분
    role = os.getenv("LAMBDA_ROLE")  # e.g., scheduler, crawler, mongo_saver, post_generator, rds_saver
    print(f"▶️ Executing Lambda with role={role}, event={event}")
    
    # ----------------- Scheduler -----------------
    if role == "scheduler":
        db: Session = SessionLocal()
        try:
            # 오늘 경기 기반 SQS 전송용 job 생성
            sqs_messages = setup_game_day_jobs(db)
            if sqs_messages:
                send_sqs_messages(sqs_messages)
                print(f"✅ 오늘 경기 기반 SQS 스케줄 생성 완료, 총 {len(sqs_messages)}개 job")
            else:
                print("🕒 오늘 경기 기반 job 없음")
            return {"statusCode": 200, "body": "Daily Game Schedule Registered"}
        finally:
            db.close()
    
    # ----------------- Crawler -----------------
    elif role == "crawler":
        topic = event.get("topic")
        if not topic:
            return {"statusCode": 400, "body": "Missing topic for crawler"}
        
        crawl_result = crawler_handler(event, context)  # 크롤러 실행
        send_sqs_message({"task": "save_to_mongo", "data": crawl_result}) # SQS 메시지 전송
        return {"statusCode": 200, "body": "Crawling done and message sent to SQS"}
    
    # ----------------- Mongo Saver -----------------
    elif role == "mongo_saver":
        # SQS 메시지로 전달된 데이터 저장
        task = event.get("task")
        if task == "save_to_mongo":
            data = event.get("data")
            mongo_saver_handler({"data": data}, context)
            return {"statusCode": 200, "body": "Data saved to MongoDB"}
        else:
            return {"statusCode": 400, "body": "Unknown task for mongo_saver"}

    # ----------------- Post Generator -----------------
    elif role == "post_generator":
        bot_type = event.get("bot_type")
        topic = event.get("topic")

        if not bot_type:
            return {"statusCode": 400, "body": "Missing bot_type"}

        if bot_type == "pregame":
            run_pregame_bot(topic)
        elif bot_type == "realtime":
            run_realtime_bot(topic)
        elif bot_type == "postgame":
            run_postgame_focus_bot(topic)
        elif bot_type == "trend":
            run_trend_bot()
        else:
            return {"statusCode": 400, "body": "Invalid bot_type"}

        return {"statusCode": 200, "body": "Bot executed"}

    # ----------------- RDS Saver -----------------
    elif role == "rds_saver":
        return rds_handler(event, context)

    # ----------------- Unknown -----------------
    else:
        return {"statusCode": 400, "body": f"Unknown LAMBDA_ROLE: {role}"}