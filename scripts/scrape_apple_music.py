import os
from playwright.sync_api import sync_playwright
from openpyxl import Workbook

OUTPUT_DIR = "captures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_sections(country, url):

    print(f"[LOG] Extracting: {country} / {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        # ⭐⭐ Apple Music Shadow DOM 강제 열기용 JS ⭐⭐
        page.wait_for_timeout(3000)

        # 섹션 제목 강제 추출
        # Apple Music은 <h2> 태그로 섹션 제목을 표시함
        titles = page.eval_on_selector_all(
            "h2",
            "elements => elements.map(el => el.innerText.trim())"
        )

        browser.close()

        return titles


def save_excel(country, titles):

    excel_path = os.path.join(OUTPUT_DIR, f"{country}_sections.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.append(["Index", "Section Title"])

    for i, t in enumerate(titles, start=1):
        ws.append([i, t])

    wb.save(excel_path)
    print(f"[LOG] Excel saved → {excel_path}")


# 실행 대상
targets = {
    "KR": "https://music.apple.com/kr/browse",
    "US": "https://music.apple.com/us/browse"
}

for country, url in targets.items():
    titles = extract_sections(country, url)
    print(f"[LOG] {country} found {len(titles)} sections")
    save_excel(country, titles)

print("[DONE]")
