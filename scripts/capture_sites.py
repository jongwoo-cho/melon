import os
import time
from datetime import datetime
import pytz
import glob
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

# --- 폴더 생성
os.makedirs("screenshots", exist_ok=True)

# --- 타임스탬프
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

# --- Chrome 옵션 (headless 안정 모드)
chrome_options = Options()
chrome_options.add_argument("--headless")  # ✅ old headless로 변경
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")
chrome_options.add_experimental_option("prefs", {
    "intl.accept_languages": "ko-KR,ko,en-US"
})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# --- 팝업 제거 스크립트
def remove_popups():
    js = """
    const selectors = [
      'div[role="dialog"]', '.popup', '#popLayer', '.dimmed',
      '.ly_popup', '.layer_popup', 'iframe', '#appPopup',
      '.wrap_popup', '.popup_area', '.modal', '.ad_banner'
    ];
    selectors.forEach(sel => document.querySelectorAll(sel).forEach(e => e.remove()));
    window.alert = () => {};
    window.confirm = () => true;
    window.prompt = () => '';
    """
    driver.execute_script(js)

# --- 안전한 접속
def safe_get(url):
    driver.get(url)
    time.sleep(4)
    remove_popups()
    time.sleep(1)

# --- 사이트 캡처
def capture_site(name, url, scroll_target=None):
    print(f"[+] Capturing {name} ...")
    safe_get(url)
    if scroll_target:
        try:
            driver.execute_script(f"document.querySelector('{scroll_target}').scrollIntoView();")
            time.sleep(2)
        except Exception as e:
            print(f"[!] scroll failed for {name}: {e}")

    path = f"screenshots/{name}_{timestamp}.png"
    driver.save_screenshot(path)
    print(f"✅ {name} captured → {path}")

# --- 대상 사이트
sites = [
    ("melon", "https://www.melon.com/", "div#new_song"),
    ("genie", "https://www.genie.co.kr/", "div.newest"),
    ("bugs", "https://music.bugs.co.kr/", "section#newAlbum"),
    ("flo", "https://www.music-flo.com/", "div.sectionNewRelease")
]

for name, url, target in sites:
    capture_site(name, url, target)

driver.quit()

# --- PDF 병합
pdf = FPDF(unit='mm', format='A4')
png_files = sorted(glob.glob('screenshots/*.png'))
if png_files:
    for img in png_files:
        pdf.add_page()
        pdf.image(img, x=0, y=0, w=210)
    pdf_path = f"screenshots/music_capture_{timestamp}.pdf"
    pdf.output(pdf_path)
    print(f"📄 PDF saved → {pdf_path}")
    for f in png_files:
        os.remove(f)
else:
    print("⚠ No screenshots found.")
