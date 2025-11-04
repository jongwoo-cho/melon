import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from fpdf import FPDF

# 📁 저장 폴더 생성
os.makedirs("screenshots", exist_ok=True)

# 🕒 한국 시간 기준 타임스탬프
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

# 🌐 Chrome 설정
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--lang=ko-KR")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def remove_popups():
    """공통 팝업 제거용 스크립트"""
    js_code = """
        const selectors = [
            'iframe', '#appPopup', '#intro_popup', '#welcomePopup',
            '#eventLayer', '#layerEvent', '#popup-prm', '#kakaoAdArea',
            '.popup', '.layer_popup', '.modal', '.dimmed', '.banner_area'
        ];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove());
        });
    """
    driver.execute_script(js_code)

def capture_site(name, url, scroll_target=None):
    """사이트 접속 및 캡처"""
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(5)
    remove_popups()
    time.sleep(2)

    if scroll_target:
        try:
            element = driver.find_element(By.CSS_SELECTOR, scroll_target)
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Scroll target not found for {name}: {e}")

    remove_popups()
    time.sleep(1)
    driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")
    print(f"✅ {name} captured")

# 🎵 사이트별 캡처
capture_site("melon", "https://www.melon.com/")
capture_site("genie", "https://www.genie.co.kr/")
capture_site("bugs", "https://music.bugs.co.kr/")
capture_site("flo", "https://www.music-flo.com/", scroll_target="section[data-testid='newReleaseTodaySection']")

driver.quit()

# 📄 PDF 병합
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=10)

for site in ["melon", "genie", "bugs", "flo"]:
    path = f"screenshots/{site}_{timestamp}.png"
    if os.path.exists(path):
        pdf.add_page()
        pdf.set_font("Helvetica", size=16)
        pdf.cell(0, 10, site.upper(), ln=True, align="C")
        pdf.image(path, x=10, y=30, w=190)

pdf_filename = f"screenshots/music_sites_{timestamp}.pdf"
pdf.output(pdf_filename)
print(f"📁 PDF created: {pdf_filename}")
