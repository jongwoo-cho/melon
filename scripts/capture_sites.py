import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image

# KST 시간
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
timestamp = now.strftime("%y%m%d_%H%M")

# 저장 폴더
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 사이트 정보
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# Chrome 옵션
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")  # 지니 한글 깨짐 방지

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

captured_files = []

def capture_site(name, url):
    driver.get(url)
    time.sleep(5)  # 페이지 로딩 대기

    # 플로 스크롤 조정
    if name == "flo":
        driver.execute_script("window.scrollTo(0, 500)")  # 오늘 발매 영역 노출
        time.sleep(1)

    # 팝업 제거
    try:
        if name == "bugs":
            # 벅스 팝업 제거 강화
            driver.execute_script("""
                const popupSelectors = [
                    '.popup', '#popup', '.dimmed', '.overlay', '.modal', '.layer_popup'
                ];
                popupSelectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            """)
    except Exception as e:
        print(f"[!] Popup removal failed for {name}: {e}")

    time.sleep(1)

    screenshot_path = os.path.join(OUTPUT_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)
    captured_files.append(screenshot_path)
    print(f"✅ {name} captured → {screenshot_path}")

for site_name, site_url in SITES.items():
    capture_site(site_name, site_url)

driver.quit()

# PNG → PDF
pdf_path = os.path.join(OUTPUT_DIR, f"music_capture_{timestamp}.pdf")
pdf = FPDF()
for img_file in captured_files:
    img = Image.open(img_file)
    pdf_w, pdf_h = 210, 297  # A4
    img_w, img_h = img.size
    ratio = min(pdf_w / img_w, pdf_h / img_h)
    pdf_w_scaled, pdf_h_scaled = img_w * ratio, img_h * ratio
    pdf.add_page()
    pdf.image(img_file, x=0, y=0, w=pdf_w_scaled, h=pdf_h_scaled)

pdf.output(pdf_path)
print(f"✅ PDF created → {pdf_path}")

# PNG 삭제
for f in captured_files:
    os.remove(f)
