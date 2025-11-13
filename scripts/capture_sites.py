import os
from datetime import datetime
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from fpdf import FPDF
import pytz

# -------------------
# 설정
# -------------------
KST = pytz.timezone("Asia/Seoul")
SAVE_FOLDER = "screenshots"
os.makedirs(SAVE_FOLDER, exist_ok=True)

SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# -------------------
# Chrome 옵션
# -------------------
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--lang=ko-KR")  # 한글 폰트

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# -------------------
# 팝업 제거 함수
# -------------------
def remove_popups():
    js = """
    let modals = document.querySelectorAll('[class*="popup"], [class*="layer"], [class*="modal"]');
    modals.forEach(m => m.style.display = 'none');
    let overlays = document.querySelectorAll('[class*="overlay"], [class*="dim"]');
    overlays.forEach(o => o.style.display = 'none');
    """
    try:
        driver.execute_script(js)
    except:
        pass

# -------------------
# 캡처
# -------------------
images = []
for name, url in SITES.items():
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    sleep(5)  # 페이지 로딩
    remove_popups()
    sleep(2)
    
    # 전체 화면 캡처
    img_path = os.path.join(SAVE_FOLDER, f"{name}.png")
    driver.save_screenshot(img_path)
    images.append(img_path)
    print(f"✅ {name} captured → {img_path}")

driver.quit()

# -------------------
# PNG → PDF
# -------------------
if images:
    now = datetime.now(KST).strftime("%y%m%d_%H%M")
    pdf_path = os.path.join(SAVE_FOLDER, f"music_capture_{now}.pdf")
    
    pdf = FPDF()
    for img_file in images:
        im = Image.open(img_file)
        pdf_w, pdf_h = 210, 297  # A4
        width, height = im.size
        ratio = min(pdf_w/width*25.4/72, pdf_h/height*25.4/72)
        pdf.add_page()
        pdf.image(img_file, x=0, y=0, w=width*ratio, h=height*ratio)
        os.remove(img_file)  # PNG 삭제

    pdf.output(pdf_path)
    print(f"✅ PDF saved → {pdf_path}")
