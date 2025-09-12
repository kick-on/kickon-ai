from sqlalchemy.orm import Session
from typing import List
from app.models.game import Game
from app.models.team import Team
from datetime import datetime, date, timedelta, timezone

def get_game_topics(
    db: Session,
    start_date: date,
    end_date: date
) -> List[str]:
    """
    특정 기간 내 경기에 대해 'Home Away 하이라이트' 형태의 토픽 리스트 반환
    """
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)

    games = (
        db.query(Game)
        .filter(Game.started_at >= start_dt, Game.started_at < end_dt)
        .all()
    )

    print(f"[DEBUG] {len(games)} games found between {start_date} and {end_date}")

    team_dict = {team.pk: team.name_kr for team in db.query(Team).all()}

    topics = []
    for game in games:
        home = team_dict.get(game.home_team_pk, "알 수 없음")
        away = team_dict.get(game.away_team_pk, "알 수 없음")
        if home and away:
            topics.append(f"{home} {away} 하이라이트")

    return topics

def has_game_today(db: Session):
    """오늘 날짜에 해당하는 경기 목록을 반환. 없으면 빈 리스트."""
    now = datetime.now(timezone.utc)
    today = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
    tomorrow = today + timedelta(days=1)

    games = (
        db.query(Game)
        .filter(Game.started_at >= today)
        .filter(Game.started_at < tomorrow)
        .all()
    )

    return games    