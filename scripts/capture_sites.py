import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

# 사이트 리스트
sites = [
    {"name": "melon", "url": "https://www.melon.com/"},
    {"name": "genie", "url": "https://www.genie.co.kr/"},
    {"name": "bugs", "url": "https://music.bugs.co.kr/"},
    {"name": "flo", "url": "https://www.music-flo.com/"},
]

# 절대 경로로 screenshots 폴더 생성
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "..", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 크롬 옵션 (팝업 및 리디렉션 차단)
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-popup-blocking")  # 팝업 차단
chrome_options.add_argument("--disable-notifications")   # 알림 차단
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--headless=new")  # GitHub Actions에서도 동작

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 한국 시간 기준 timestamp
kst = pytz.timezone("Asia/Seoul")
ts = datetime.now(kst).strftime("%y%m%d_%H%M")

screenshots = []

for site in sites:
    name = site["name"]
    url = site["url"]
    print(f"[+] Capturing {name} ...")
    try:
        driver.get(url)
        time.sleep(8)  # JS 렌더링 충분히 기다리기

        # 전체 페이지 높이 설정
        full_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 1080)")
        driver.set_window_size(1920, full_height)

        filename = os.path.join(SCREENSHOT_DIR, f"{name}_{ts}.png")
        driver.save_screenshot(filename)
        screenshots.append(filename)
        print(f"✅ {name} captured → {filename}")
    except Exception as e:
        print(f"[!] {name}: capture failed → {e}")

driver.quit()

# PNG → PDF 변환
pdf_filename = os.path.join(SCREENSHOT_DIR, f"music_capture_{ts}.pdf")
pdf = FPDF(unit="mm", format="A4")

for img_path in screenshots:
    if os.path.exists(img_path):
        pdf.add_page()
        pdf.image(img_path, x=0, y=0, w=210, h=297)
    else:
        print(f"⚠️ File not found: {img_path}")

pdf.output(pdf_filename)
print(f"✅ PDF created → {pdf_filename}")
