import os
import time
import pytz
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF  # PDF 변환용

# =========================================================
# 기본 설정
# =========================================================
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# KST 시간 기준 파일명
kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)
timestamp = now_kst.strftime("%y%m%d_%H%M")
pdf_filename = os.path.join(OUTPUT_DIR, f"screenshots_{timestamp}.pdf")

# =========================================================
# 공통 함수
# =========================================================
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1440,3000")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--lang=ko-KR")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--blink-settings=imagesEnabled=true")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


def try_js(script):
    try:
        driver.execute_script(script)
    except Exception:
        pass


def send_escape_multiple(times=5, delay=0.2):
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    for _ in range(times):
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(delay)


def hide_high_zindex_overlays():
    try_js("""
      (function(){
        const els = Array.from(document.querySelectorAll('*'));
        els.forEach(e=>{
          try {
            const s = window.getComputedStyle(e);
            const z = parseInt(s.zIndex)||0;
            if(z >= 999){
              e.style.display='none';
              e.style.visibility='hidden';
            }
          } catch(err){}
        });
      })();
    """)


def mutation_cleanup(duration=5, interval=0.5):
    end = time.time() + duration
    while time.time() < end:
        hide_high_zindex_overlays()
        time.sleep(interval)


# =========================================================
# 사이트별 팝업 제거
# =========================================================
def handle_melon():
    print("[INFO] Handling Melon popup...")
    try_js("""
      document.querySelectorAll('#popNotice, .layer_ad, #adPop, .pop_wrap, .popup, .layer_popup, .dimmed, .modal').forEach(e=>e.remove());
      document.body.style.overflow='auto';
    """)
    send_escape_multiple(5, 0.2)
    hide_high_zindex_overlays()
    print("[INFO] Melon cleanup done.")


def handle_genie():
    print("[INFO] Handling Genie popup...")

    # iframe 및 광고 제거
    try_js("""
      (function() {
        const iframes = document.querySelectorAll('iframe');
        for (let i=0; i<iframes.length; i++) {
          try {
            const f = iframes[i];
            const src = f.src || '';
            if (src.includes('popup') || src.includes('ad') || src.includes('event') || src.includes('banner')) {
              f.remove();
            } else if (f.contentWindow && f.contentWindow.document) {
              f.contentWindow.document.body.innerHTML = '';
            }
          } catch(e) {}
        }
      })();
    """)

    # 팝업, dimmed, layer 제거
    try_js("""
      document.querySelectorAll(
        '#popup, #pop, .popup, .popdim, .poplayer, .ly_popup, .ly_wrapper, .layer_popup, .modal, .dimmed, .ad_layer, .mask, .overlay, [id*="pop"], [class*="pop"]'
      ).forEach(e => e.remove());
      document.body.style.overflow = 'auto';
    """)

    hide_high_zindex_overlays()
    send_escape_multiple(6, 0.2)

    # 한글 폰트 깨짐 방지
    try_js("""
      var meta = document.createElement('meta');
      meta.setAttribute('charset','UTF-8');
      document.head.appendChild(meta);
      document.querySelectorAll('*').forEach(e=>{
        try{ e.style.fontFamily='NanumGothic, Arial, sans-serif'; }catch(err){}
      });
    """)
    print("[INFO] Genie cleanup done.")


def handle_bugs():
    print("[INFO] Handling Bugs popup...")
    try_js("""
      document.querySelectorAll('.layer_popup, .popup, .ad_layer, .modal, .dimmed, .mask, [id*="popup"]').forEach(e=>e.remove());
      document.body.style.overflow='auto';
    """)
    send_escape_multiple(4, 0.2)
    hide_high_zindex_overlays()
    print("[INFO] Bugs cleanup done.")


def handle_flo():
    print("[INFO] Handling FLO popup...")
    try_js("""
      document.querySelectorAll('.popup, .modal, .dimmed, .layer, .banner, [id*="pop"]').forEach(e=>e.remove());
      document.body.style.overflow='auto';
    """)
    send_escape_multiple(4, 0.2)
    hide_high_zindex_overlays()
    print("[INFO] FLO cleanup done.")


# =========================================================
# PDF 저장 함수
# =========================================================
def save_to_pdf(driver, pdf, selector=None):
    tmp_png = os.path.join(OUTPUT_DIR, "tmp.png")

    if selector:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            element.screenshot(tmp_png)
        except Exception as e:
            print(f"[WARN] Element not found for selector: {selector}, full page screenshot instead.")
            driver.save_screenshot(tmp_png)
    else:
        driver.save_screenshot(tmp_png)

    pdf.add_page()
    pdf.image(tmp_png, x=10, y=10, w=180)
    os.remove(tmp_png)


# =========================================================
# 메인 실행
# =========================================================
if __name__ == "__main__":
    driver = init_driver()
    sites = [
        ("Melon", "https://www.melon.com/chart/index.htm", handle_melon, None),
        ("Genie", "https://www.genie.co.kr/chart/top200", handle_genie, None),
        ("Bugs", "https://music.bugs.co.kr/chart", handle_bugs, None),
        # FLO: 오늘 발매 음악 섹션만 캡처
        ("FLO", "https://www.music-flo.com/browse", handle_flo, 'section[data-testid*="today"]')
    ]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)

    for name, url, handler, selector in sites:
        print(f"[INFO] Visiting {name}...")
        driver.get(url)
        time.sleep(6)
        handler()

        print(f"[INFO] Capturing {name}...")
        save_to_pdf(driver, pdf, selector=selector)

    pdf.output(pdf_filename)
    print(f"[INFO] All captures saved as PDF: {pdf_filename}")
    driver.quit()
