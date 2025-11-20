import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image

# selenium helpers
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

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
chrome_options.add_argument("--lang=ko-KR")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 10)

captured_files = []

# -----------------------------------------------------------
# 🔥 벅스 전용 강력 팝업 제거
# -----------------------------------------------------------
def remove_bugs_popups(driver, timeout=6.0):
    try:
        # 기본적인 close 버튼 클릭
        close_btns = ['.pop_close', '.btn_close', '.btn-close', '.close', '.layerClose']
        for sel in close_btns:
            for el in driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    el.click()
                except:
                    driver.execute_script("arguments[0].click();", el)

        # ESC 키 전송
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            for _ in range(3):
                body.send_keys(Keys.ESCAPE)
                time.sleep(0.3)
        except:
            pass

        # 강력 DOM 제거
        js = """
        const selectors = [
            '#layPop', '#layer_pop', '#popup', '#popupLayer', '.layer-popup',
            '.pop_layer', '.popup', '.modal', '.modal-bg', '.modal-backdrop',
            '.dimmed', '.dimmedLayer', '.popdim', '.ly_wrap', '.ly_pop', '.pop_wrap',
            '.eventLayer', '.evt_layer'
        ];
        selectors.forEach(sel=>document.querySelectorAll(sel).forEach(el=>el.remove()));
        document.body.style.overflow='auto';
        document.documentElement.style.overflow='auto';
        """
        driver.execute_script(js)
        time.sleep(0.5)
        return True
    except:
        return False

# -----------------------------------------------------------
# 🔵 FLO — 오늘 발매 음악 10곡 캡처용 스크롤
# -----------------------------------------------------------
def scroll_flo(driver):
    try:
        # 오늘 발매 음악 섹션 위치로 이동
        target = driver.find_element(By.XPATH, "//*[contains(text(), '오늘 발매')]")
        driver.execute_script("arguments[0].scrollIntoView({block:'start'});", target)
        time.sleep(1)
        # 섹션 아래 2~3곡 정도 더 보여지도록 추가 스크롤
        driver.execute_script("window.scrollBy(0, 350);")  # 충분히 아래로
        time.sleep(1)
    except:
        # fallback
        driver.execute_script("window.scrollTo(0, 900)")
        time.sleep(1)

# -----------------------------------------------------------
# 사이트별 캡처
# -----------------------------------------------------------
def capture_site(name, url):
    driver.get(url)
    time.sleep(5)

    if name == "flo":
        scroll_flo(driver)
    elif name == "bugs":
        for _ in range(3):
            remove_bugs_popups(driver, timeout=3)
            time.sleep(0.6)
    else:
        try:
            driver.execute_script("""
                document.querySelectorAll('[class*="popup"], [id*="popup"], .dimmed, .overlay, .modal')
                    .forEach(e => e.remove());
                document.body.style.overflow='auto';
                document.documentElement.style.overflow='auto';
            """)
        except:
            pass

    time.sleep(1)
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
# PNG → PDF 변환
# -----------------------------------------------------------
pdf_path = os.path.abspath(os.path.join(OUTPUT_DIR, f"music_capture_{timestamp}.pdf"))
pdf = FPDF()

for img_file in captured_files:
    img = Image.open(img_file)
    pdf_w, pdf_h = 210, 297
    img_w, img_h = img.size
    ratio = min(pdf_w / img_w, pdf_h / img_h)
    pdf_w_scaled, pdf_h_scaled = img_w * ratio, img_h * ratio

    pdf.add_page()
    pdf.image(img_file, x=0, y=0, w=pdf_w_scaled, h=pdf_h_scaled)

pdf.output(pdf_path)
print(f"✅ PDF saved → {pdf_path}")

# PNG 삭제
for f in captured_files:
    os.remove(f)
