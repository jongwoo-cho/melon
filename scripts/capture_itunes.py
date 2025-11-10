from playwright.sync_api import sync_playwright
import os
from datetime import datetime
import pandas as pd

# 설정
countries = {
    "KR": "kr",
    "US": "us",
    "JP": "jp",
    "TH": "th",
    "HK": "hk",
    "CN": "cn"
}

sections = {
    "New Releases": "new-releases",
    "Most Played": "most-played"
}

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d")

# 결과 저장용
all_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for country_name, code in countries.items():
        for section_name, feed in sections.items():
            # iTunes RSS JSON Feed 사용
            url = f"https://rss.applemarketingtools.com/api/v2/{code}/music/{feed}/10/albums.json"
            page.goto(url)
            page.wait_for_timeout(2000)  # 안전 대기

            # JSON 데이터 가져오기
            content = page.locator("body").inner_text()
            import json
            data = json.loads(content)

            for item in data['feed']['results']:
                all_data.append({
                    "국가": country_name,
                    "섹션": section_name,
                    "앨범명": item['name'],
                    "아티스트": item['artistName'],
                    "링크": item['url']
                })

        # 스크린샷 저장 (브라우저로 실제 둘러보기 페이지 캡처)
        browse_url = f"https://music.apple.com/{code}/browse"
        page.goto(browse_url)
        page.wait_for_timeout(5000)
        screenshot_path = os.path.join(output_dir, f"{country_name}_browse_{timestamp}.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Captured {screenshot_path}")

    browser.close()

# Excel로 저장
df = pd.DataFrame(all_data)
excel_path = os.path.join(output_dir, f"iTunes_Data_{timestamp}.xlsx")
df.to_excel(excel_path, index=False)
print(f"Saved Excel: {excel_path}")
