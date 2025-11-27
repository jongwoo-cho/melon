import os
from datetime import datetime
from openpyxl import Workbook
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials


# =============================
# 1. 환경 변수 (GitHub Actions에 등록 필요)
# =============================
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


if not CLIENT_ID or not CLIENT_SECRET:
raise Exception("SPOTIFY_CLIENT_ID 또는 SPOTIFY_CLIENT_SECRET 환경 변수가 없습니다.")


# =============================
# 2. 캡처 폴더 생성
# =============================
OUTPUT_DIR = "captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================
# 3. Spotify API 인증
# =============================
sp = Spotify(auth_manager=SpotifyClientCredentials(
client_id=CLIENT_ID,
client_secret=CLIENT_SECRET
))


# =============================
# 4. 플레이리스트 수집
# =============================
PLAYLIST_ID = "37i9dQZF1DX9tPFwDMOaN1"
playlist = sp.playlist_items(PLAYLIST_ID, additional_types=["track"], limit=100)


tracks = playlist.get("items", [])


# =============================
# 5. 엑셀 파일 생성
# =============================
now = datetime.now().strftime("%Y-%m-%d")
excel_path = os.path.join(OUTPUT_DIR, f"spotify_kpop_{now}.xlsx")
wb = Workbook()
ws = wb.active
ws.append(["순서", "곡 제목", "아티스트", "플레이리스트 추가 날짜"])


for idx, item in enumerate(tracks, start=1):
track = item.get("track", {})
title = track.get("name", "")
artists = ", ".join([a["name"] for a in track.get("artists", [])])


added_at = item.get("added_at", "")
added_at = added_at.split("T")[0] if added_at else ""


ws.append([idx, title, artists, added_at])


wb.save(excel_path)
print(f"엑셀 저장 완료 → {excel_path}")
