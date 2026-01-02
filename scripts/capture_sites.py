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

# -----------------------------------------------------------
# KST 시간
# -----------------------------------------------------------
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
timestamp = now.strftime("%y%m%d_%H%M")

# -----------------------------------------------------------
# 저장 폴더
# -----------------------------------------------------------
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------
# 사이트 정보
# -----------------------------------------------------------
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
    "vibe": "https://vibe.naver.com/today"
}

# -----------------------------------------------------------
# Chrome 옵션
# -----------------------------------------------------------
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
wait = WebDriverWait(driver, 10)

captured_files = []

# -----------------------------------------------------------
# 벅스 팝업 제거 (강화 버전)
# -----------------------------------------------------------
def remove_bugs_popups(driver, timeout=6.0):
    try:
        close_btn_selectors = [
            ".pop_close", ".btn_close", ".btn-close", ".close",
            ".layerClose", ".btnClose", ".lay-close", ".btnClosePop"
        ]

        for sel in close_btn_selectors:
            for e in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    e.click()
                except:
                    try:
                        driver.execute_script("arguments[0].click();", e)
                    except:
                        pass

        texts = ["닫기", "×", "✕", "Close"]
        for t in texts:
            for e in driver.find_elements(By.XPATH, f"//*[text()[normalize-space()='{t}']]"):
                try:
                    e.click()
                except:
                    try:
                        driver.execute_script("arguments[0].click();", e)
                    except:
                        pass

        try:
            body = driver.find_element(By.TAG_NAME, "body")
            for _ in range(3):
                body.send_keys(Keys.ESCAPE)
                time.sleep(0.2)
        except:
            pass

        driver.execute_script("""
            const selectors = [
                '#layPop','#layer_pop','#popup','.popup','.modal',
                '.modal-backdrop','.dimmed','.dimmedLayer',
                '.layer-popup','.pop_layer','.eventLayer'
            ];
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        """)

        time.sleep(0.5)
        return True
    except:
        return False

# -----------------------------------------------------------
# FLO 처리 (기존 그대로)
# -----------------------------------------------------------
def handle_flo(driver):
    try:
        driver.execute_script("""
            let sel = [
                '.popup','.pop','.modal','.layer',
                '[class*="Popup"]','[id*="popup"]',
                '.cookie','.cookie-popup'
            ];
            sel.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        """)
    except:
        pass

    time.sleep(1)

    try:
        total_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, total_height + 200)
        time.sleep(1)
    except:
        pass

# -----------------------------------------------------------
# VIBE 팝업 제거
# -----------------------------------------------------------
def handle_vibe(driver):
    try:
        driver.execute_script("""
            let sel = ['.popup','.modal','.layer','.dimmed','[role="dialog"]'];
            sel.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        """)
    except:
        pass
    time.sleep(1)

# -----------------------------------------------------------
# 사이트 캡처
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

        # ✅ 벅스 캡처 위치 고정 (이 부분만 추가됨)
        try:
            driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(0.5)
        except:
            pass

    elif name == "vibe":
        handle_vibe(driver)

    else:
        try:
            driver.execute_script("""
                document.querySelectorAll(
                    '[class*="popup"],[id*="popup"],.dimmed,.overlay,.modal'
                ).forEach(e => e.remove());
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
            """)
        except:
            pass

    screenshot_path = os.path.join(OUTPUT_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)
    captured_files.append(screenshot_path)
    print(f"✅ {name} captured → {screenshot_path}")

# -----------------------------------------------------------
# 실행
# -----------------------------------------------------------
for site_name, site_url in SITES.items():
    capture_site(site_name, site_url)

driver.quit()

# -----------------------------------------------------------
# PNG → PDF
# -----------------------------------------------------------
pdf_path = os.path.join(OUTPUT_DIR, f"music_capture_{timestamp}.pdf")
pdf = FPDF()

for img_file in captured_files:
    img = Image.open(img_file)
    img_w, img_h = img.size
    pdf_w, pdf_h = 210, 297
    ratio = min(pdf_w / img_w, pdf_h / img_h)

    pdf.add_page()
    pdf.image(
        img_file,
        x=0,
        y=0,
        w=img_w * ratio,
        h=img_h * ratio
    )

pdf.output(pdf_path)
print(f"✅ PDF saved → {pdf_path}")

# -----------------------------------------------------------
# PNG 삭제
# -----------------------------------------------------------
for f in captured_files:
    os.remove(f)
