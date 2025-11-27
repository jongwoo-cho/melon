import os
import pandas as pd
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup

# Spotify K-Pop ON! 플레이리스트 HTML 요청
playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DX9tPFwDMOaN1"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

res = requests.get(playlist_url, headers=headers)
if res.status_code != 200:
    raise Exception(f"페이지 요청 실패: {res.status_code}")

html = res.text

# BeautifulSoup으로 곡 정보 추출
soup = BeautifulSoup(html, "html.parser")

tracks = []

# Spotify 웹 페이지는 JS 렌더링 방식이므로 일부 정보는 HTML에 없음
track_elements = soup.find_all("div", {"class": "tracklist-row__name"})

for i, elem in enumerate(track_elements, start=1):
    title_elem = elem.find("span")
    if title_elem:
        title = title_elem.get_text(strip=True)
    else:
        title = "알 수 없음"

    artist_elem = elem.find_next_sibling("a")
    if artist_elem:
        artists = artist_elem.get_text(strip=True)
    else:
        artists = "알 수 없음"

    added_at = "알 수 없음"
    tracks.append([i, title, artists, added_at])

# spotify 폴더 자동 생성
output_dir = "spotify"
os.makedirs(output_dir, exist_ok=True)

# 엑셀 파일 저장
kst = pytz.timezone("Asia/Seoul")
date_str = datetime.now(kst).strftime("%Y-%m-%d")

df = pd.DataFrame(tracks, columns=["순서", "제목", "아티스트명", "추가한 날짜"])
file_path = f"{output_dir}/spotify_kpop_on_{date_str}.xlsx"
df.to_excel(file_path, index=False)

print(f"Saved: {file_path}")
