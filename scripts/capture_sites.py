import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
import time

# 사이트 목록
sites = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# 저장 폴더
os.makedirs("screenshots", exist_ok=True)

# Chrome 옵션
chrome_options = Options()
chrome_options.add_argument("--headless=new")          # headless 모드
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--lang=ko-KR")            # 한글 폰트

# 드라이버 실행
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

screenshots = []

def capture_site(name, url):
    driver.get(url)
    time.sleep(5)  # 페이지 로딩 대기
    # 팝업 제거 JS
    js_remove = """
    let els = document.querySelectorAll('[style*="position: fixed"], .popup, .modal, .dimmed');
    els.forEach(e => e.remove());
    """
    driver.execute_script(js_remove)
    # 스크린샷 저장
    ts = datetime.now().strftime("%y%m%d_%H%M")
    filename = f"screenshots/{name}_{ts}.png"
    driver.save_screenshot(filename)
    screenshots.append(filename)
    print(f"✅ {name} captured → {filename}")

for name, url in sites.items():
    capture_site(name, url)

driver.quit()

# PDF 생성
pdf_filename = f"screenshots/music_capture_{datetime.now().strftime('%y%m%d_%H%M')}.pdf"
pdf = FPDF()
for img_path in screenshots:
    pdf.add_page()
    pdf.image(img_path, x=0, y=0, w=210, h=297)  # A4 기준
pdf.output(pdf_filename)
print(f"✅ PDF saved → {pdf_filename}")
