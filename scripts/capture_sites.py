import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from fpdf import FPDF

# ───────────────────────────────
# 기본 설정
# ───────────────────────────────
os.makedirs("screenshots", exist_ok=True)
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

chrome_options = Options()
chrome_options.add_argument("--headless")
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
# 공통 팝업 제거 함수
# ───────────────────────────────
def brutal_popup_killer():
    js = """
        try {
            // 모든 iframe 제거
            document.querySelectorAll('iframe').forEach(f => f.remove());

            // 팝업, 레이어, 모달로 보이는 요소 제거
            const popupLike = [
                'popup', 'layer', 'modal', 'banner', 'dim', 'ad', 'event', 'appdown'
            ];
            document.querySelectorAll('*').forEach(el => {
                const id = el.id ? el.id.toLowerCase() : '';
                const cls = el.className ? el.className.toString().toLowerCase() : '';
                const style = window.getComputedStyle(el);
                if (
                    popupLike.some(k => id.includes(k) || cls.includes(k)) ||
                    style.position === 'fixed' && style.zIndex > '100'
                ) {
                    el.remove();
                }
            });

            // shadow DOM 내부 제거 시도
            document.querySelectorAll('*').forEach(e => {
                if (e.shadowRoot) {
                    e.shadowRoot.querySelectorAll('*').forEach(child => {
                        const id = child.id ? child.id.toLowerCase() : '';
                        const cls = child.className ? child.className.toString().toLowerCase() : '';
                        if (popupLike.some(k => id.includes(k) or cls.includes(k))) {
                            child.remove();
                        }
                    });
                }
            });

            // body 스크롤 복원
            document.body.style.overflow = 'auto';
        } catch(e) { console.error(e); }
    """
    driver.execute_script(js)

# ───────────────────────────────
# 사이트별 처리 로직
# ───────────────────────────────
def capture_site(name, url, scroll_target=None):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(6)
    brutal_popup_killer()
    time.sleep(2)

    # 사이트별 추가 제거 코드
    if name == "melon":
        driver.execute_script("""
            document.querySelectorAll('#popNotice, #layer_popup, #intro_popup, .notice_layer').forEach(e=>e.remove());
            document.querySelectorAll('iframe').forEach(f=>f.remove());
        """)

    elif name == "genie":
        driver.execute_script("""
            document.querySelectorAll('#popLayer, .main-popup, .dimmed, #event_layer, .layer_popup').forEach(e=>e.remove());
            document.querySelectorAll('iframe').forEach(f=>f.remove());
        """)

    elif name == "bugs":
        driver.execute_script("""
            document.querySelectorAll('#popLayer, #appBanner, #welcomePopup, .popup, .layer, .dimmed').forEach(e=>e.remove());
        """)

    elif name == "flo":
        driver.execute_script("""
            document.querySelectorAll('.popup, .modal, .banner, .overlay, .appdown').forEach(e=>e.remove());
            window.scrollTo(0, document.body.scrollHeight / 3);
        """)

    time.sleep(2)
    brutal_popup_killer()
    time.sleep(1)

    # 스크롤 대상 있으면 이동
    if scroll_target:
        try:
            element = driver.find_element(By.CSS_SELECTOR, scroll_target)
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Scroll target not found for {name}: {e}")

    # 스크린샷 저장
    screenshot_path = f"screenshots/{name}_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"✅ {name} captured → {screenshot_path}")

# ───────────────────────────────
# 사이트 리스트
# ───────────────────────────────
sites = {
    "melon": "https://www.melon.com/index.htm",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

for name, url in sites.items():
    capture_site(name, url, scroll_target="section[data-testid='newReleaseTodaySection']" if name == "flo" else None)

driver.quit()

# ───────────────────────────────
# PDF 생성
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
