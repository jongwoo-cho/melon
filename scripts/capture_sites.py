import os
import time
import base64
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

# -------------------------------
# 환경 설정
# -------------------------------
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--lang=ko-KR")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# -------------------------------
# 사이트 목록
# -------------------------------
SITES = {
    "melon": "https://www.melon.com/index.htm",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# -------------------------------
# 팝업 제거
# -------------------------------
def remove_popups():
    js = """
    try {
        const keywords = ['popup','layer','modal','banner','ad','event','notice','promotion','app','install','download'];
        document.querySelectorAll('*').forEach(el => {
            const id = el.id ? el.id.toLowerCase() : '';
            const cls = el.className ? el.className.toString().toLowerCase() : '';
            const style = window.getComputedStyle(el);
            if (keywords.some(k => id.includes(k) || cls.includes(k)) || (style.position === 'fixed' && parseInt(style.zIndex) > 100)) {
                el.remove();
            }
        });
        document.querySelectorAll('iframe').forEach(f => f.remove());
        document.body.style.overflow = 'auto';
    } catch(e) {}
    """
    try:
        driver.execute_script(js)
    except Exception:
        pass

# -------------------------------
# 페이지 전체 렌더링 대기
# -------------------------------
def wait_full_render(timeout=60):
    """MutationObserver 기반 JS 렌더링 완료 대기"""
    wait_script = """
    const callback = arguments[0];
    try {
        let lastHeight = document.body.scrollHeight;
        let sameCount = 0;
        const observer = new MutationObserver(() => {
            const newHeight = document.body.scrollHeight;
            if (Math.abs(newHeight - lastHeight) < 5) sameCount++;
            else sameCount = 0;
            lastHeight = newHeight;
        });
        observer.observe(document.body, {childList:true, subtree:true, attributes:true});
        const checkInterval = setInterval(() => {
            if (sameCount > 15) { observer.disconnect(); clearInterval(checkInterval); callback(true); }
        }, 500);
    } catch(e) { callback(true); }
    """
    try:
        driver.set_script_timeout(timeout)
        driver.execute_async_script(wait_script)
    except Exception:
        time.sleep(3)

# -------------------------------
# 전체 페이지 캡처
# -------------------------------
def capture_site(name, url):
    print(f"[+] Capturing {name} ...")
    try:
        driver.get(url)
        WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
        remove_popups()
        wait_full_render()
        remove_popups()
        time.sleep(1)

        # 전체 높이 계산
        full_height = driver.execute_script("""
            return Math.max(
                document.body ? document.body.scrollHeight : 1080,
                document.documentElement ? document.documentElement.scrollHeight : 1080
            );
        """)

        driver.set_window_size(1920, full_height)
        time.sleep(1)

        # CDP 전체 캡처
        screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        img_path = f"{OUTPUT_DIR}/{name}_{timestamp}.png"
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
        print(f"✅ {name} captured → {img_path}")
    except Exception as e:
        print(f"[!] {name} capture failed: {e}")

# -------------------------------
# 실행
# -------------------------------
for name, url in SITES.items():
    capture_site(name, url)

driver.quit()

# -------------------------------
# PDF 생성
# -------------------------------
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=10)
pdf.set_font("Helvetica", size=16)

for site in SITES.keys():
    img_file = f"{OUTPUT_DIR}/{site}_{timestamp}.png"
    if os.path.exists(img_file):
        pdf.add_page()
        pdf.cell(0, 10, site.upper(), ln=True, align="C")
        pdf.image(img_file, x=10, y=30, w=190)

pdf_file = f"{OUTPUT_DIR}/music_sites_{timestamp}.pdf"
pdf.output(pdf_file)
print(f"📁 PDF created: {pdf_file}")
