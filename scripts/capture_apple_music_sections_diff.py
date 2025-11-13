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

# 저장 폴더
output_dir = "captures"
os.makedirs(output_dir, exist_ok=True)

# 날짜 기준 파일명
timestamp = datetime.now().strftime("%Y%m%d")
excel_filename = f"{output_dir}/AppleMusic_Sections_{timestamp}.xlsx"

all_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for country, url in urls.items():
        page.goto(url)
        page.wait_for_timeout(7000)  # 페이지 렌더 대기

        # 영역별로 노출된 컨텐츠 추출
        sections = ["New", "Latest Song", "New Releases", "Trending Songs"]
        for section_name in sections:
            try:
                # 섹션 찾기
                section = page.locator(f"h2:text('{section_name}')").locator("..")
                items = section.locator("li")
                
                for i in range(items.count()):
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
                        "순서": i+1,
                        "앨범명/대표텍스트": album_name,
                        "아티스트": artist_name
                    })
            except Exception as e:
                print(f"Error extracting {section_name} for {country}: {e}")

    browser.close()

# Excel 저장
df = pd.DataFrame(all_data)
df.to_excel(excel_filename, index=False)
print(f"Saved Excel: {excel_filename}")
