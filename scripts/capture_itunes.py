from playwright.sync_api import sync_playwright
import os
from datetime import datetime

# 캡처할 URL 목록
urls = {
    "KR": "https://music.apple.com/kr/browse",
    "US": "https://music.apple.com/us/browse",
    "JP": "https://music.apple.com/jp/browse",
    "TH": "https://music.apple.com/th/browse",
    "HK": "https://music.apple.com/hk/browse",
    "CN": "https://music.apple.com/cn/browse"
}

# 캡처 저장 폴더
output_dir = "captures"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    for country, url in urls.items():
        page.goto(url)
        page.wait_for_timeout(5000)  # 페이지 로딩 대기 (5초)

        # 전체 페이지 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{output_dir}/{country}_browse_{timestamp}.png"
        page.screenshot(path=filename, full_page=True)
        print(f"Captured {filename}")
    
    browser.close()
