from app.db.sql.session import SessionLocal
from app.services.board_service import save_generated_post
import json

def lambda_handler(event, context):
    data = json.loads(event['Records'][0]['body'])

    db = SessionLocal()
    save_generated_post(
        db=db,
        user_pk=data["user_pk"],
        title=data["title"],
        contents=data["contents"],
        has_image=False
    )
    db.close()