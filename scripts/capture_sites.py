import os
import time
import base64
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF


# ────────────── 환경 설정 ──────────────
os.makedirs("screenshots", exist_ok=True)
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
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


# ────────────── 팝업 강제 제거 ──────────────
def brutal_popup_killer():
    js = """
    try {
      const keywords = ['popup','layer','modal','banner','ad','event','notice','promotion','app','install','download'];
      document.querySelectorAll('*').forEach(el => {
        const id = el.id ? el.id.toLowerCase() : '';
        const cls = el.className ? el.className.toString().toLowerCase() : '';
        const style = window.getComputedStyle(el);
        if (
          keywords.some(k => id.includes(k) || cls.includes(k)) ||
          (style.position === 'fixed' && parseInt(style.zIndex) > 100)
        ) {
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


# ────────────── 렌더링 완료 대기 ──────────────
def wait_until_render_stable(timeout=50):
    """MutationObserver + scrollHeight 안정화 대기"""
    check_script = """
        let lastHeight = document.body.scrollHeight;
        let sameCount = 0;
        const observer = new MutationObserver(() => {
            const newHeight = document.body.scrollHeight;
            if (Math.abs(newHeight - lastHeight) < 10) sameCount++;
            else sameCount = 0;
            lastHeight = newHeight;
        });
        observer.observe(document.body, {childList:true, subtree:true, attributes:true});
        return new Promise(resolve => {
            const timer = setInterval(() => {
                if (sameCount > 20) { observer.disconnect(); clearInterval(timer); resolve(true); }
            }, 500);
        });
    """
    try:
        driver.set_script_timeout(timeout)
        driver.execute_async_script(check_script)
    except Exception:
        time.sleep(3)


# ────────────── 페이지 전체 스크롤 및 렌더링 완료 대기 ──────────────
def ensure_full_render():
    try:
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        current = 0
        while current < scroll_height:
            driver.execute_script(f"window.scrollTo(0, {current});")
            time.sleep(0.8)
            current += 800
            scroll_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, 0);")
        wait_until_render_stable()
    except Exception:
        time.sleep(2)


# ────────────── 전체 페이지 캡처 ──────────────
def capture_full_page(name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(5)  # 첫 페이지 로드 대기
    brutal_popup_killer()
    ensure_full_render()
    brutal_popup_killer()
    time.sleep(1)

    # 화면 높이 계산
    full_height = driver.execute_script("""
        return Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight,
            1080
        );
    """)

    driver.set_window_size(1920, full_height)
    time.sleep(1)

    # CDP 캡처
    try:
        screenshot = driver.execute_cdp_cmd(
            "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True}
        )
        img_path = f"screenshots/{name}_{timestamp}.png"
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
        print(f"✅ {name} captured → {img_path}")
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
    img_path = f"screenshots/{site}_{timestamp}.png"
    if os.path.exists(img_path):
        pdf.add_page()
        pdf.cell(0, 10, site.upper(), ln=True, align="C")
        pdf.image(img_path, x=10, y=30, w=190)

pdf_filename = f"screenshots/music_sites_{timestamp}.pdf"
pdf.output(pdf_filename)
print(f"📁 PDF created: {pdf_filename}")
