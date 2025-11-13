import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

# 저장 폴더
SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

# KST 시간
kst = pytz.timezone('Asia/Seoul')
now = datetime.now(kst)
timestamp = now.strftime("%y%m%d_%H%M")

# 사이트 정보
sites = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# 크롬 옵션
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")  # 팝업 차단
chrome_options.add_argument("--disable-notifications")   # 알림 차단
chrome_options.add_argument("--start-maximized")         # 전체화면

# 드라이버
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 팝업 제거 함수
def remove_popups():
    try:
        driver.execute_script("""
            let elements = document.querySelectorAll('div, iframe, button');
            elements.forEach(el => {
                if(el.offsetHeight > 0 && el.offsetWidth > 0 && (el.style.position === 'fixed' || el.style.zIndex > 1000)){
                    el.style.display = 'none';
                }
            });
        """)
    except:
        pass

# 스크린샷 캡처
png_files = []
for name, url in sites.items():
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(5)  # 페이지 로딩 대기
    remove_popups()
    time.sleep(1)
    file_path = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(file_path)
    png_files.append(file_path)
    print(f"✅ {name} captured → {file_path}")

driver.quit()

# PNG → PDF
pdf_path = os.path.join(SAVE_DIR, f"music_capture_{timestamp}.pdf")
pdf = FPDF(unit="pt", format=[1920, 1080])
for img in png_files:
    pdf.add_page()
    pdf.image(img, 0, 0, 1920, 1080)
pdf.output(pdf_path)
print(f"✅ PDF saved → {pdf_path}")

# PNG 파일 제거 (PDF만 남기기)
for img in png_files:
    os.remove(img)
