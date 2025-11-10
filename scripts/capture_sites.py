import os
import time
import base64
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

# ────────────── 기본 세팅 ──────────────
os.makedirs("screenshots", exist_ok=True)
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


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


def wait_for_render_complete(timeout=40):
    """JS 렌더링 완료될 때까지 기다림"""
    start = time.time()
    last_height = 0
    while time.time() - start < timeout:
        try:
            height = driver.execute_script("return document.body.scrollHeight || 0")
            text_len = driver.execute_script("return document.body.innerText.length")
            if height > 1200 and text_len > 500:
                return True
            time.sleep(1)
            if abs(height - last_height) < 20:
                continue
            last_height = height
        except:
            time.sleep(1)
    return False


def capture_full_page(name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)

    # 페이지 완전 로드 대기
    try:
        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except:
        print(f"[!] {name}: readyState timeout")

    # JS 렌더링 완료 대기
    if not wait_for_render_complete():
        print(f"[!] {name}: render timeout (empty body)")

    # 팝업 제거
    brutal_popup_killer()
    time.sleep(2)

    # 전체 높이 계산
    try:
        full_height = driver.execute_script("""
            return Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                1080
            );
        """)
    except:
        full_height = 1080

    driver.set_window_size(1920, full_height)
    time.sleep(1)

    # 캡처
    screenshot_path = f"screenshots/{name}_{timestamp}.png"
    try:
        screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
        print(f"✅ {name} captured → {screenshot_path}")
    except Exception as e:
        print(f"[!] {name} capture failed: {e}")


# ────────────── 대상 사이트 ──────────────
sites = {
    "melon": "https://www.melon.com/index.htm",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

for name, url in sites.items():
    capture_full_page(name, url)

driver.quit()

# ────────────── PDF 병합 ──────────────
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
