import os
import pandas as pd
from datetime import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import subprocess

# 1. Spotify K-Pop ON! 스크래핑
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

# 2. Excel 저장
output_dir = "spotify"
os.makedirs(output_dir, exist_ok=True)

kst = pytz.timezone("Asia/Seoul")
date_str = datetime.now(kst).strftime("%Y-%m-%d")
file_name = f"spotify_kpop_on_{date_str}.xlsx"
file_path = os.path.join(output_dir, file_name)

df = pd.DataFrame(tracks, columns=["순서", "제목", "아티스트명", "추가한 날짜"])
df.to_excel(file_path, index=False)
print(f"Saved: {file_path}")

# 3. Git add, commit, push (멜론 캡처 방식 그대로)
subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
subprocess.run(["git", "config", "--global", "user.email", "github-actions@github.com"], check=True)
subprocess.run(["git", "add", file_path], check=True)
subprocess.run(["git", "commit", "-m", f"Daily Spotify scrape - {date_str}"], check=True)
subprocess.run(["git", "push", "origin", "main"], check=True)
print(f"Pushed {file_name} to GitHub")
