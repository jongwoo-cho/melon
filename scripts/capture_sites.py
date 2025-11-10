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
import base64

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
    } catch(e) { console.error(e); }
    """
    try:
        driver.execute_script(js)
    except Exception as e:
        print(f"[!] popup_killer error: {e}")

# ───────────────────────────────
# 전체 페이지 캡처 함수
# ───────────────────────────────
def capture_full_page(name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)

    # 페이지 완전히 로딩될 때까지 대기
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # 주요 콘텐츠 엘리먼트 로딩 대기
    content_targets = {
        "melon": "div.wrap_main_chart",
        "genie": "div#wrap, main, div.main-contents",
        "bugs": "div#container, div#gnb, div#contentArea",
        "flo": "div#root, section[data-testid='newReleaseTodaySection']"
    }
    selector = content_targets.get(name, "body")

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    except:
        print(f"[!] {name}: main content load timeout")

    time.sleep(3)
    brutal_popup_killer()
    time.sleep(2)

    # lazy load 스크롤
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        for y in range(0, last_height, 800):
            driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(0.3)
        driver.execute_script("window.scrollTo(0, 0);")
    except:
        pass

    # 전체 높이 계산 및 설정
    full_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 1080)")
    driver.set_window_size(1920, full_height)
    time.sleep(1)

    # 더 안정적인 캡처 (Chrome DevTools Protocol)
    screenshot_path = f"screenshots/{name}_{timestamp}.png"
    screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
    with open(screenshot_path, "wb") as f:
        f.write(base64.b64decode(screenshot["data"]))

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
# PDF 합치기
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
