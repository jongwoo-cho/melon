import os
import pandas as pd
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup

# Spotify K-Pop ON! 플레이리스트 URL
playlist_url = "https://open.spotify.com/playlist/37i9dQZF1DX9tPFwDMOaN1"
headers = {"User-Agent": "Mozilla/5.0"}

res = requests.get(playlist_url, headers=headers)
if res.status_code != 200:
    raise Exception(f"페이지 요청 실패: {res.status_code}")

html = res.text
soup = BeautifulSoup(html, "html.parser")

tracks = []
track_elements = soup.find_all("div", {"class": "tracklist-row__name"})

for i, elem in enumerate(track_elements, start=1):
    title_elem = elem.find("span")
    title = title_elem.get_text(strip=True) if title_elem else "알 수 없음"

    artist_elem = elem.find_next_sibling("a")
    artists = artist_elem.get_text(strip=True) if artist_elem else "알 수 없음"

    added_at = "알 수 없음"
    tracks.append([i, title, artists, added_at])

# spotify 폴더 자동 생성
output_dir = "spotify"
os.makedirs(output_dir, exist_ok=True)

kst = pytz.timezone("Asia/Seoul")
date_str = datetime.now(kst).strftime("%Y-%m-%d")

file_name = f"spotify_kpop_on_{date_str}.xlsx"
file_path = os.path.join(output_dir, file_name)

df = pd.DataFrame(tracks, columns=["순서", "제목", "아티스트명", "추가한 날짜"])
df.to_excel(file_path, index=False)

print(f"Saved: {file_path}")
