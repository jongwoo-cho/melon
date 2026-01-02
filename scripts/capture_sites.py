import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from fpdf import FPDF
from PIL import Image

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# KST 시간
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
timestamp = now.strftime("%y%m%d_%H%M")

# 저장 폴더
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 사이트 정보 (✅ VIBE 추가)
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
    "vibe": "https://vibe.naver.com/today"
}

# Chrome 옵션
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 10)

captured_files = []

# -----------------------------------------------------------
# 벅스 팝업 제거 (기존 그대로)
# -----------------------------------------------------------
def remove_bugs_popups(driver, timeout=6.0):
    try:
        close_btn_selectors = [
            ".pop_close", ".btn_close", ".btn-close", ".close", ".layerClose",
            ".btnClose", ".lay-close", ".btnClosePop", ".pop_btn_close"
        ]
        for sel in close_btn_selectors:
            for e in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", e)
                    e.click()
                except:
                    pass

        for _ in range(3):
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.2)
            except:
                pass

        driver.execute_script("""
            const sel = [
                '.popup','.modal','.dimmed','.layer-popup',
                '.eventLayer','.evt_layer','.ly_pop','.pop_layer'
            ];
            sel.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
            document.body.style.overflow='auto';
            document.documentElement.style.overflow='auto';
        """)
        time.sleep(1)
        return True
    except:
        return False

# -----------------------------------------------------------
# FLO (기존 그대로)
# -----------------------------------------------------------
def handle_flo(driver):
    try:
        driver.execute_script("""
            let sel = [
                '.popup', '.pop', '.modal', '.layer',
                '[class*="Popup"]', '[id*="popup"]'
            ];
            sel.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
            document.body.style.overflow='auto';
            document.documentElement.style.overflow='auto';
        """)
    except:
        pass

    time.sleep(1)
    try:
        h = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, h + 200)
    except:
        pass

# -----------------------------------------------------------
# ✅ VIBE 팝업 제거 (신규)
# -----------------------------------------------------------
def handle_vibe(driver):
    try:
        # ESC 반복
        body = driver.find_element(By.TAG_NAME, "body")
        for _ in range(4):
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.2)
    except:
        pass

    try:
        driver.execute_script("""
            const sel = [
                '.popup','.modal','.layer','.dimmed',
                '[class*="popup"]','[class*="layer"]',
                '[id*="popup"]','[id*="layer"]',
                '.app_download','.login_layer'
            ];
            sel.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
            document.body.style.overflow='auto';
            document.documentElement.style.overflow='auto';
        """)
    except:
        pass

    time.sleep(1)

# -----------------------------------------------------------
# 사이트별 캡처
# -----------------------------------------------------------
def capture_site(name, url):
    driver.get(url)
    time.sleep(5)

    if name == "flo":
        handle_flo(driver)
    elif name == "bugs":
        for _ in range(2):
            remove_bugs_popups(driver, timeout=3.0)
            time.sleep(0.5)
    elif name == "vibe":
        handle_vibe(driver)
    else:
        try:
            driver.execute_script("""
                document.querySelectorAll(
                    '[class*="popup"],[id*="popup"],.modal,.dimmed'
                ).forEach(e => e.remove());
                document.body.style.overflow='auto';
                document.documentElement.style.overflow='auto';
            """)
        except:
            pass

    time.sleep(1)
    path = os.path.join(OUTPUT_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(path)
    captured_files.append(path)
    print(f"✅ {name} captured → {path}")

# -----------------------------------------------------------
# 실행
# -----------------------------------------------------------
for n, u in SITES.items():
    capture_site(n, u)

driver.quit()

# -----------------------------------------------------------
# PNG → PDF
# -----------------------------------------------------------
pdf_path = os.path.join(OUTPUT_DIR, f"music_capture_{timestamp}.pdf")
pdf = FPDF()

for img_file in captured_files:
    img = Image.open(img_file)
    w, h = img.size
    ratio = min(210 / w, 297 / h)
    pdf.add_page()
    pdf.image(img_file, x=0, y=0, w=w * ratio, h=h * ratio)

pdf.output(pdf_path)
print(f"✅ PDF saved → {pdf_path}")

# PNG 삭제
for f in captured_files:
    os.remove(f)
