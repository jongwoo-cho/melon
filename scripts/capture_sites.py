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

# screenshots 폴더 확인
os.makedirs("screenshots", exist_ok=True)

# 서울 시간
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

# 크롬 옵션 (팝업 차단, 폰트 깨짐 방지 등)
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-translate")
chrome_options.add_argument("--lang=ko-KR")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.popups": 0,
    "intl.accept_languages": "ko-KR,ko"
})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def safe_get(url):
    """사이트 접속 + 팝업 제거 로직"""
    driver.get(url)
    time.sleep(4)
    driver.execute_script("""
        const selectors = ['div[role="dialog"]', '.popup', '#popLayer', '.dimmed', 
                           '.ly_popup', '.layer_popup', 'iframe', '#appPopup'];
        selectors.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
        window.alert = function() {};
        window.confirm = function() {return true;};
        window.prompt = function() {return '';};
    """)
    time.sleep(1)

def capture_site(name, url, scroll_target=None):
    """사이트 캡처 함수"""
    print(f"▶ {name} 캡처 중...")
    safe_get(url)

    # 지정된 영역으로 스크롤
    if scroll_target:
        try:
            driver.execute_script(f"document.querySelector('{scroll_target}').scrollIntoView();")
            time.sleep(2)
        except Exception as e:
            print(f"⚠ {name}: 스크롤 실패 ({e})")

    path = f"screenshots/{name}_{timestamp}.png"
    driver.save_screenshot(path)
    print(f"✅ {name} 캡처 완료 → {path}")

# 사이트별 캡처 설정
sites = [
    ("melon", "https://www.melon.com/", "div#new_song"),
    ("genie", "https://www.genie.co.kr/", "div.newest"),
    ("bugs", "https://music.bugs.co.kr/", "section#newAlbum"),
    ("flo", "https://www.music-flo.com/", "div.sectionNewRelease")
]

for name, url, target in sites:
    capture_site(name, url, target)

driver.quit()

# PDF로 병합
pdf = FPDF(unit='mm', format='A4')
png_files = sorted(glob.glob('screenshots/*.png'))

if not png_files:
    print("⚠ PNG 파일이 없습니다.")
else:
    for img_path in png_files:
        pdf.add_page()
        pdf.image(img_path, x=0, y=0, w=210)
    pdf_path = f"screenshots/music_capture_{timestamp}.pdf"
    pdf.output(pdf_path)
    print(f"📄 PDF 생성 완료 → {pdf_path}")

    # PNG 삭제
    for f in png_files:
        os.remove(f)
    print("🧹 PNG 파일 삭제 완료.")
