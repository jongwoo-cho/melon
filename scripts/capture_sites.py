import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from fpdf import FPDF

# 📁 스크린샷 폴더
os.makedirs("screenshots", exist_ok=True)

# 🕒 한국 시간 기준 타임스탬프
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

# 🌐 Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--lang=ko-KR")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36"
)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 팝업 제거용 공통 함수
def remove_popups():
    js = """
        const selectors = [
            'iframe', '#appPopup', '#intro_popup', '#welcomePopup',
            '#eventLayer', '#layerEvent', '#popup-prm', '#kakaoAdArea',
            '.popup', '.layer_popup', '.modal', '.dimmed', '.banner_area',
            '.ad_wrap', '.modal-content', '#popLayer'
        ];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => el.remove());
        });
        document.body.style.overflow = 'auto';
    """
    driver.execute_script(js)

# 사이트별 캡처 함수
def capture_site(name, url, scroll_target=None):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(6)
    remove_popups()
    time.sleep(2)

    # 특수 처리 (지니/플로 팝업 등)
    if name == "genie":
        try:
            driver.execute_script("document.querySelectorAll('.main-popup, .dimmed').forEach(e=>e.remove());")
        except Exception:
            pass

    if name == "flo":
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        except Exception:
            pass

    # 스크롤 대상 있으면 이동
    if scroll_target:
        try:
            element = driver.find_element(By.CSS_SELECTOR, scroll_target)
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Scroll target not found for {name}: {e}")

    remove_popups()
    time.sleep(1)
    driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")
    print(f"✅ {name} captured")

# 🎵 사이트별 URL
sites = {
    "melon": "https://www.melon.com/index.htm",  # 차트 리디렉션 방지
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# 각 사이트 캡처 실행
for name, url in sites.items():
    capture_site(name, url, scroll_target="section[data-testid='newReleaseTodaySection']" if name == "flo" else None)

driver.quit()

# 📄 PDF 병합
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
