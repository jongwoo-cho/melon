from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import os

# 국가별 Apple Music Browse URL
urls = {
    "KR": "https://music.apple.com/kr/browse",
    "US": "https://music.apple.com/us/browse",
    "JP": "https://music.apple.com/jp/browse",
    "TH": "https://music.apple.com/th/browse",
    "HK": "https://music.apple.com/hk/browse",
    "CN": "https://music.apple.com/cn/browse"
}

# 저장 폴더 (없으면 자동 생성)
output_dir = "captures"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Created folder: {output_dir}")

# 날짜별 파일명
timestamp = datetime.now().strftime("%Y%m%d")
excel_filename = f"{output_dir}/AppleMusic_Sections_{timestamp}.xlsx"

all_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for country, url in urls.items():
        page.goto(url)
        page.wait_for_timeout(7000)  # 페이지 렌더 대기

        # 모든 section 순회
        sections = page.locator("section")
        for s_idx in range(sections.count()):
            sec = sections.nth(s_idx)
            try:
                section_title = sec.locator("h2").inner_text().strip()
            except:
                continue
            if section_title not in ["New", "Latest Song", "New Releases", "Trending Songs"]:
                continue

            # 해당 섹션 내부 아이템 추출
            items = sec.locator("div[role='group'] a")
            for i in range(items.count()):
                item = items.nth(i)
                try:
                    album_name = item.locator("span").nth(0).inner_text().strip()
                except:
                    album_name = ""
                try:
                    artist_name = item.locator("span").nth(1).inner_text().strip()
                except:
                    artist_name = ""

                all_data.append({
                    "국가": country,
                    "섹션": section_title,
                    "순서": i+1,
                    "앨범명/대표텍스트": album_name,
                    "아티스트": artist_name
                })

    browser.close()

# 데이터 확인용 콘솔 출력 (선택)
for entry in all_data[:10]:  # 앞 10개만 샘플 출력
    print(entry)

# Excel 저장
if all_data:
    df = pd.DataFrame(all_data)
    df.to_excel(excel_filename, index=False)
    print(f"\nSaved Excel: {excel_filename}")
else:
    print("\nNo data extracted. Check selectors or page structure.")
