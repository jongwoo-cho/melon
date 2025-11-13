import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image

# -----------------------------
# 환경 설정
# -----------------------------
os.makedirs("screenshots", exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.notifications": 2,
    "profile.default_content_setting_values.popups": 2,
    "profile.default_content_setting_values.automatic_downloads": 1
})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# -----------------------------
# 캡처 함수
# -----------------------------
def capture_site(name, url, scroll=False, click_latest=False):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(6)

    # 팝업 제거 시도
    for script in [
        "document.querySelectorAll('iframe, .ad, .popup, .layer_popup, .banner, [id*=\"pop\"], [class*=\"pop\"]').forEach(e=>e.remove());",
        "if(window.confirm) window.confirm=function(){return false;};",
        "if(window.alert) window.alert=function(){};"
    ]:
        driver.execute_script(script)
    time.sleep(1)

    # 멜론은 상단 최신음악만 캡처
    if name == "melon":
        element = driver.find_element(By.CSS_SELECTOR, "#new_album, .new_album, #conts_section, #wrap")
        element.screenshot(f"screenshots/{name}_{timestamp}.png")
        print(f"✅ {name} captured")
        return

    # FLO는 '오늘 발매 음악' 영역
    if name == "flo":
        try:
            section = driver.find_element(By.XPATH, "//h2[contains(text(),'오늘 발매')]/ancestor::section")
            section.screenshot(f"screenshots/{name}_{timestamp}.png")
            print(f"✅ {name} captured")
            return
        except Exception:
            pass

    # 전체 스크롤 캡처 (기본)
    S = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, S)
    time.sleep(1)
    driver.save_screenshot(f"screenshots/{name}_{timestamp}.png")
    print(f"✅ {name} captured")

# -----------------------------
# 대상 사이트 목록
# -----------------------------
timestamp = datetime.now().strftime("%y%m%d_%H%M")
sites = {
    "melon": "https://www.melon.com/new/index.htm",
    "genie": "https://www.genie.co.kr/newest",
    "bugs": "https://music.bugs.co.kr/newest/album",
    "flo": "https://www.music-flo.com/browse/new"
}

for name, url in sites.items():
    try:
        capture_site(name, url)
    except Exception as e:
        print(f"[!] {name} capture failed: {e}")

driver.quit()

# -----------------------------
# PDF 생성
# -----------------------------
pdf_path = f"screenshots/music_capture_{timestamp}.pdf"
c = canvas.Canvas(pdf_path, pagesize=A4)
width, height = A4

for site in sites.keys():
    img_path = f"screenshots/{site}_{timestamp}.png"
    if os.path.exists(img_path):
        img = Image.open(img_path)
        iw, ih = img.size
        ratio = min(width / iw, height / ih)
        c.drawImage(img_path, 0, 0, iw * ratio, ih * ratio)
        c.showPage()

c.save()

# PNG 삭제 (PDF만 남김)
for f in os.listdir("screenshots"):
    if f.endswith(".png"):
        os.remove(os.path.join("screenshots", f))

print(f"✅ PDF created: {pdf_path}")
