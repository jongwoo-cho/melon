from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import os

# 국가별 iTunes "둘러보기" URL
urls = {
    "KR": "https://music.apple.com/kr/browse",
    "US": "https://music.apple.com/us/browse",
    "JP": "https://music.apple.com/jp/browse",
    "TH": "https://music.apple.com/th/browse",
    "HK": "https://music.apple.com/hk/browse",
    "CN": "https://music.apple.com/cn/browse"
}

# 저장 폴더 생성
output_dir = "captures"
os.makedirs(output_dir, exist_ok=True)

# 날짜 기준 파일명
timestamp = datetime.now().strftime("%Y%m%d")
excel_filename = f"{output_dir}/iTunes_Data_{timestamp}.xlsx"

all_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for country, url in urls.items():
        page.goto(url)
        page.wait_for_timeout(7000)  # 페이지 로딩 충분히 대기

        # 전체 페이지 캡처
        screenshot_path = f"{output_dir}/{country}_browse_{timestamp}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Captured page: {screenshot_path}")

        # 각 섹션별 앨범/아티스트 추출
        # iTunes 페이지 구조 기준 (섹션 제목 h2, 앨범 li)
        sections = ["New", "Latest Song", "New Releases", "Trending Songs"]

        for section_name in sections:
            try:
                # 섹션 찾기 (h2 텍스트로 검색)
                section_locator = page.locator(f"h2:text('{section_name}')").locator("..")
                items = section_locator.locator("li")

                count = items.count()
                for i in range(count):
                    try:
                        album_name = items.nth(i).locator("h3").inner_text()
                    except:
                        album_name = ""
                    try:
                        artist_name = items.nth(i).locator("h4").inner_text()
                    except:
                        artist_name = ""
                    all_data.append({
                        "국가": country,
                        "섹션": section_name,
                        "앨범명": album_name,
                        "아티스트": artist_name
                    })
            except Exception as e:
                print(f"Error extracting {section_name} for {country}: {e}")

    browser.close()

# Excel 저장
df = pd.DataFrame(all_data)
df.to_excel(excel_filename, index=False)
print(f"Saved Excel: {excel_filename}")
