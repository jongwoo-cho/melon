import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from fpdf import FPDF

# ───────────────────────────────
# 기본 설정
# ───────────────────────────────
os.makedirs("screenshots", exist_ok=True)
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--lang=ko-KR")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# ───────────────────────────────
# 팝업 제거 함수
# ───────────────────────────────
def brutal_popup_killer():
    js = """
    try {
        const popupLike = ['popup','layer','modal','banner','dim','ad','event','appdown','notice'];
        document.querySelectorAll('*').forEach(el => {
            const id = el.id ? el.id.toLowerCase() : '';
            const cls = el.className ? el.className.toString().toLowerCase() : '';
            const style = window.getComputedStyle(el);
            if (
                popupLike.some(k => id.includes(k) || cls.includes(k)) ||
                (style.position === 'fixed' && parseInt(style.zIndex) > 100)
            ) el.remove();
        });
        document.querySelectorAll('iframe').forEach(f => f.remove());
        document.body.style.overflow = 'auto';
    } catch(e) { console.error(e); }
    """
    driver.execute_script(js)

# ───────────────────────────────
# 전체화면 캡처 함수
# ───────────────────────────────
def capture_full_page(name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)

    # 페이지 로드 완료 대기
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except:
        pass

    # JS 렌더링 대기
    time.sleep(8)

    # 팝업 제거 2회
    brutal_popup_killer()
    time.sleep(2)
    brutal_popup_killer()

    # 페이지 전체 높이로 캡처
    full_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, full_height)
    time.sleep(1)

    screenshot_path = f"screenshots/{name}_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"✅ {name} captured → {screenshot_path}")

# ───────────────────────────────
# 사이트 목록
# ───────────────────────────────
sites = {
    "melon": "https://www.melon.com/index.htm",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

for name, url in sites.items():
    capture_full_page(name, url)

driver.quit()

# ───────────────────────────────
# PDF 병합
# ───────────────────────────────
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=10)
pdf.set_font("Helvetica", size=16)

for site in sites.keys():
    path = f"screenshots/{site}_{timestamp}.png"
    if os.path.exists(path):
        pdf.add_page()
        pdf.cell(0, 10, site.upper(), ln=True, align="C")
        pdf.image(path, x=10, y=30, w=190)

pdf_filename = f"screenshots/music_sites_{timestamp}.pdf"
pdf.output(pdf_filename)
print(f"📁 PDF created: {pdf_filename}")
