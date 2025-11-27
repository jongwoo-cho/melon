import os
import pandas as pd
from datetime import datetime
import pytz
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

# ------------------------------------------------------
# 0. Spotify API 인증 (환경변수에 ID/SECRET 필요)
# ------------------------------------------------------
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

if not client_id or not client_secret:
    raise Exception("환경변수 SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET 설정 필요!")

sp = Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

# ------------------------------------------------------
# 1. K-Pop ON! 플레이리스트 데이터 가져오기
# ------------------------------------------------------
playlist_id = "37i9dQZF1DX9tPFwDMOaN1"

results = sp.playlist_items(playlist_id, additional_types=["track"], limit=100)

tracks = []
order = 1

for item in results["items"]:
    track = item["track"]
    if not track:
        continue

    title = track["name"]
    artists = ", ".join([a["name"] for a in track["artists"]])
    added_at = item["added_at"]

    tracks.append([order, title, artists, added_at])
    order += 1

# ------------------------------------------------------
# 2. 엑셀로 저장
# ------------------------------------------------------
kst = pytz.timezone("Asia/Seoul")
date_str = datetime.now(kst).strftime("%Y-%m-%d")

df = pd.DataFrame(tracks, columns=["순서", "제목", "아티스트명", "추가한 날짜"])

output_dir = "spotify"
os.makedirs(output_dir, exist_ok=True)

file_path = f"{output_dir}/spotify_kpop_on_{date_str}.xlsx"
df.to_excel(file_path, index=False)

print(f"Saved: {file_path}")
