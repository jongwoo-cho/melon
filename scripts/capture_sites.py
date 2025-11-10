import os
import time
from datetime import datetime
import pytz
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

# ────────────── 기본 설정 ──────────────
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


# ────────────── 팝업 제거 ──────────────
def brutal_popup_killer():
    js = """
    try {
        const keywords = ['popup','layer','modal','banner','dim','ad','event','app','notice','download','promotion'];
        document.querySelectorAll('*').forEach(el => {
            const id = el.id ? el.id.toLowerCase() : '';
            const cls = el.className ? el.className.toString().toLowerCase() : '';
            const style = window.getComputedStyle(el);
            if (
                keywords.some(k => id.includes(k) || cls.includes(k)) ||
                (style.position === 'fixed' && parseInt(style.zIndex) > 100)
            ) el.remove();
        });
        document.querySelectorAll('iframe').forEach(f => f.remove());
        document.body.style.overflow = 'auto';
    } catch(e) {}
    """
    try:
        driver.execute_script(js)
    except:
        pass


# ────────────── 전체 캡처 ──────────────
def capture_full_page(name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)

    # 페이지 로드 대기
    try:
        WebDriverWait(driver, 40).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except:
        print(f"[!] {name}: page load timeout")

    # body가 생길 때까지 기다리기
    for _ in range(20):
        body_exists = driver.execute_script("return !!document.body")
        if body_exists:
            break
        time.sleep(1)
    else:
        print(f"[!] {name}: body not found, skipping scrollHeight check")

    # 팝업 제거
    time.sleep(5)
    brutal_popup_killer()
    time.sleep(2)

    # 스크롤 시뮬레이션
    try:
        last_height = driver.execute_script("return document.body.scrollHeight || 2000")
        for y in range(0, last_height, 800):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
    except Exception as e:
        print(f"[!] scroll error: {e}")

    # 전체 높이 계산
    try:
        full_height = driver.execute_script("""
            return Math.max(
                document.body.scrollHeight || 0,
                document.documentElement.scrollHeight || 0,
                1080
            );
        """)
    except:
        full_height = 1080

    driver.set_window_size(1920, full_height)
    time.sleep(1)

    # 캡처 실행
    screenshot_path = f"screenshots/{name}_{timestamp}.png"
    try:
        screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
        print(f"✅ {name} captured → {screenshot_path}")
    except Exception as e:
        print(f"[!] {name} capture failed: {e}")


# ────────────── 사이트 목록 ──────────────
sites = {
    "melon": "https://www.melon.com/index.htm",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

for name, url in sites.items():
    capture_full_page(name, url)

driver.quit()


# ────────────── PDF 저장 ──────────────
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
