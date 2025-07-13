import asyncio
import csv
import os
import random
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict

import emoji
from dotenv import load_dotenv
from twikit import Client, Tweet

KEYWORDS = ["SKT", "유심"]

TIMELINES: List[date] = [
    date(2025, 4, 18),  # 1. 침해 사실 내부 인지
    date(2025, 4, 22),  # 2. KISA 신고
    date(2025, 4, 28),  # 3. 대국민 사과
    date(2025, 5, 7),   # 4. SK그룹 회장 사과
    date(2025, 5, 19),  # 5. 민관 합동 조사 1차
    date(2025, 6, 13),  # 6. 위약금 논란 조사
    date(2025, 6, 16),  # 7. 국제 공조
    date(2025, 6, 30),  # 8. 정부 권고 & 보상안
    date(2025, 7, 4),   # 9. 최종 조사 결과 발표
    date(2025, 7, 7),   # 10. (후속 여론 확인용)
]

MAX_DATA_LIMIT = 1100

URL_RE = re.compile(r"https?://\S+|www\.\S+")

def remove_urls(text: str, repl: str = "") -> str:
    return URL_RE.sub(repl, text)

def clean_text(text: str) -> str:
    text = remove_urls(text)
    text = emoji.replace_emoji(text, "")
    return text.strip()

# try:
#     from zoneinfo import ZoneInfo
#     KST = ZoneInfo("Asia/Seoul")
# except ModuleNotFoundError:
#     import pytz
#     KST = pytz.timezone("Asia/Seoul")

TWITTER_STRFMT = "%a %b %d %H:%M:%S %z %Y"  # 'Fri Apr 18 12:34:56 +0000 2025'
TS_RE = re.compile(r"^\d{10}(?:\d{3})?$")   # 10~13자리 숫자(초/밀리초 epoch)

# def to_kst(dt_or_raw):
#     if isinstance(dt_or_raw, datetime):
#         dt = dt_or_raw
#     else:
#         raw = str(dt_or_raw)
#         if TS_RE.match(raw):
#             sec = int(raw[:10])
#             dt = datetime.fromtimestamp(sec, tz=timezone.utc)
#         else:
#             dt = datetime.strptime(raw, TWITTER_STRFMT)

#     try:
#         from zoneinfo import ZoneInfo
#         return dt.astimezone(ZoneInfo("Asia/Seoul"))
#     except ModuleNotFoundError:
#         import pytz
#         return dt.astimezone(pytz.timezone("Asia/Seoul"))

async def prevent_rate_limit(base: float = 15.5, jitter: float = 6.3) -> None:
    await asyncio.sleep(base + random.random() * jitter)

async def fetch_day(
    client: Client,
    keyword: str,
    day: date,
    limit: int,
) -> List[Dict]:
    since_str = day.isoformat()
    until_str = (day + timedelta(days=1)).isoformat()
    query = f'"{keyword}" lang:ko since:{since_str} until:{until_str}'

    print(f"▶ [{keyword}] {since_str} ~ {until_str} 수집 시작...", file=sys.stderr)
    tweets: List[Tweet] = await client.search_tweet(query, "Latest")
    results: List[Dict] = []

    async def process_page(page: List[Tweet]):
        for t in page:
            # dt_kst = to_kst(getattr(t, "created_at_datetime", t.created_at))
            dt_utc = getattr(t, "created_at_datetime", t.created_at_datetime)

            results.append(
                {
                    # "created_at": dt_kst.isoformat(sep=" ", timespec="seconds"),
                    "created_at": dt_utc.isoformat(sep=" ", timespec="seconds"),
                    "text": clean_text(t.text),
                }
            )

    await process_page(tweets)

    # 페이지네이션
    while len(results) < limit:
        next_page = await tweets.next()
        if not next_page:
            break
        await prevent_rate_limit()
        await process_page(next_page)
        tweets = next_page

    # 필요 이상으로 받았다면 잘라내기
    if len(results) > limit:
        results = results[:limit]

    print(f"  완료: {len(results):4}개", file=sys.stderr)
    return results

async def main() -> None:
    load_dotenv()

    client = Client("ko")

    if Path("cookies.json").exists():
        client.load_cookies("cookies.json")
        print("쿠키로 로그인", file=sys.stderr)
    else:
        await client.login(
            auth_info_1=os.getenv("USERNAME"),
            auth_info_2=os.getenv("EMAIL"),
            password=os.getenv("PASSWORD"),
        )
        client.save_cookies("cookies.json")
        print("로그인 및 쿠키 저장", file=sys.stderr)

    # 데이터 폴더 생성
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    tasks = []
    for anchor in TIMELINES:
        for delta in (-1, 0, 1):
            day = anchor + timedelta(days=delta)
            for kw in KEYWORDS:
                tasks.append((kw, day))

    for kw, day in tasks:
        rows = await fetch_day(client, kw, day, MAX_DATA_LIMIT)
        # 저장
        out_path = data_dir / f"{kw}_{day.strftime('%Y%m%d')}.csv"
        with out_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["created_at", "text"])
            writer.writeheader()
            writer.writerows(rows)
        # rate limit 방지
        await prevent_rate_limit()

    print("\n모든 작업 완료", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
