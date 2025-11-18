import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image

# KST 시간
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
timestamp = now.strftime("%y%m%d_%H%M")

# 저장 폴더
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 사이트 정보
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# Chrome 옵션
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,5000")
chrome_options.add_argument("--lang=ko-KR")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), 
    options=chrome_options
)

captured_files = []

# ------------------------------
# 벅스 팝업 제거 (기존 유지)
# ------------------------------
def remove_bugs_popups(driver):
    try:
        driver.execute_script("""
            const selectors = [
                '#layPop', 
                '.layer-popup', 
                '.popup', 
                '.modal',
                '.modal-bg',
                '.modal-backdrop',
                '#eventLayer'
            ];
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });

            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        """)
    except:
        pass


# ------------------------------
# 사이트별 캡처
# ------------------------------
def capture_site(name, url):
    driver.get(url)
    time.sleep(4)

    # FLO 스크롤
    if name == "flo":
        driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(1)

    # ------------------------------
    # ⭐ 벅스만 최신음악 영역 요소 캡처로 변경
    # ------------------------------
    if name == "bugs":
        remove_bugs_popups(driver)
        time.sleep(1)

        try:
            # 최신 음악 영역 선택자 (벅스 메인)
            section = driver.find_element("css selector", "section#newAlbum, section.newAlbum")

            screenshot_path = os.path.join(OUTPUT_DIR, f"{name}_{timestamp}.png")
            section.screenshot(screenshot_path)

            captured_files.append(screenshot_path)
            print(f"✅ BUGS (element capture) → {screenshot_path}")
            return

        except Exception as e:
            print("❌ Bugs element screenshot failed:", e)

    # ------------------------------
    # 다른 사이트는 기존 방식 그대로
    # ------------------------------
    else:
        try:
            driver.execute_script("""
                let elems = document.querySelectorAll('[class*="popup"], [id*="popup"], .dimmed, .overlay, .modal');
                elems.forEach(e => e.remove());
            """)
        except:
            pass

        screenshot_path = os.path.join(OUTPUT_DIR, f"{name}_{timestamp}.png")
        driver.save_screenshot(screenshot_path)
        captured_files.append(screenshot_path)
        print(f"✅ {name} captured → {screenshot_path}")


# ------------------------------
# 실행
# ------------------------------
for site_name, site_url in SITES.items():
    capture_site(site_name, site_url)

driver.quit()

# ------------------------------
# PNG → PDF 변환
# ------------------------------
pdf_path = os.path.abspath(os.path.join(OUTPUT_DIR, f"music_capture_{timestamp}.pdf"))
pdf = FPDF()

for img_file in captured_files:
    img = Image.open(img_file)
    pdf_w, pdf_h = 210, 297
    img_w, img_h = img.size
    ratio = min(pdf_w / img_w, pdf_h / img_h)
    pdf_w_scaled, pdf_h_scaled = img_w * ratio, img_h * ratio

    pdf.add_page()
    pdf.image(img_file, x=0, y=0, w=pdf_w_scaled, h=pdf_h_scaled)

pdf.output(pdf_path)
print(f"📄 PDF saved → {pdf_path}")

# PNG 삭제
for f in captured_files:
    os.remove(f)
