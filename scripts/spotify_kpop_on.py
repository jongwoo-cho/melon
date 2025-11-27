import os
import pandas as pd
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup

# --- 1. Spotify K-Pop ON! 플레이리스트 스크래핑 ---
playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DX9tPFwDMOaN1"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(playlist_url, headers=headers)
if res.status_code != 200:
    raise Exception(f"페이지 요청 실패: {res.status_code}")

html = res.text
soup = BeautifulSoup(html, "html.parser")

tracks = []
# Spotify 페이지 구조가 바뀌면 selector 수정 필요
track_elements = soup.select("div.tracklist-row__name")
for i, elem in enumerate(track_elements, start=1):
    title_elem = elem.select_one("span")
    title = title_elem.get_text(strip=True) if title_elem else "알 수 없음"
    artist_elem = elem.find_next_sibling("a")
    artists = artist_elem.get_text(strip=True) if artist_elem else "알 수 없음"
    added_at = "알 수 없음"  # HTML만으로는 날짜 확인 불가
    tracks.append([i, title, artists, added_at])

# --- 2. Excel 저장 (workflow 내부) ---
kst = pytz.timezone("Asia/Seoul")
date_str = datetime.now(kst).strftime("%Y-%m-%d")
file_name = f"spotify_kpop_on_{date_str}.xlsx"

# workflow 내부 경로
file_path = os.path.join("/github/workspace", file_name)

df = pd.DataFrame(tracks, columns=["순서", "제목", "아티스트명", "추가한 날짜"])
df.to_excel(file_path, index=False)
print(f"Saved: {file_path}")
