from youtube_comment_downloader import YoutubeCommentDownloader
from datetime import datetime, timezone, timedelta
import requests
from app.db.mongo.mongo_utils import save_youtube_comment_doc

from app.core.config import settings

API_KEY = settings.youtube_api_key

# 영상 검색 (업로드일 기준으로 필터링)
def search_videos(query, max_results=10):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance", # 관련도 중심
        "key": API_KEY
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    items = response.json()["items"]

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # 필터: 검색어의 양쪽 팀 이름이 모두 제목에 들어간 경우만 통과
    teams = [part.strip() for part in query.replace("하이라이트", "").split(" ") if part.strip()]

    # 제외할 스포츠 키워드
    excluded_keywords = ["농구", "야구", "배구"]

    filtered_items = []
    for item in items:
        title = item["snippet"]["title"].lower()

        # 1. 팀 이름 모두 포함
        if not all(team.lower() in title for team in teams):
            continue

        # 2. 제외 키워드 포함 시 skip
        if any(keyword in title for keyword in excluded_keywords):
            continue

        filtered_items.append(item)
    
    return [
        {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "published_at": item["snippet"]["publishedAt"]
        }
        for item in filtered_items
        if datetime.strptime(item["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) >= week_ago
    ]

# 댓글 크롤링 및 저장
def crawl_youtube_comments_by_query(query):
    print(f"\n🔍 [1] 검색 쿼리: {query}")

    try:
        videos = search_videos(query)
        print(f"📺 [2] 검색된 영상 수: {len(videos)}")
    except Exception as e:
        print(f"❌ 유튜브 검색 중 문제 발생: {e}")
        return
    
    downloader = YoutubeCommentDownloader()
    results = []
    
    for video in videos:
        video_id = video["video_id"]
        print(f"\n🎬 [3] 영상 제목: {video['title']} / ID: {video_id}")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        comment_data = []

        try:
            for comment in downloader.get_comments_from_url(video_url, sort_by=0):
                comment_text = comment["text"]
                comment_obj = {
                    "author": comment.get("author", "unknown"),
                    "text": comment_text,
                    "like_count": comment.get("votes", 0),
                    "published_at": datetime.now(timezone.utc),
                    "match": query,
                    "text_for_embedding": f"{video['title']}에 대한 팬 반응: {comment_text}"
                }
                comment_data.append(comment_obj)
        except Exception as e:
            print(f"❌ 댓글 크롤링 중 문제 발생: {e}")
            continue
        
        print(f"✅ [4] 댓글 수집 완료: {len(comment_data)}개")

        if len(comment_data) == 0:
            print(f"❌ 댓글 없음")
            continue

        doc = {
            "source": "youtube",
            "video_id": video_id,
            "video_title": video["title"],
            "video_url": video_url,
            "team_mentioned": query,
            "match_date": None,
            "video_published_at": datetime.strptime(video["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc),
            "crawled_at": datetime.now(timezone.utc),
            "comments": comment_data
        }

        results.append(doc)

    return results