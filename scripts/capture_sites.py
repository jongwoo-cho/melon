import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader

# ✅ 한글 폰트 등록
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

# ✅ 저장 경로
os.makedirs("screenshots", exist_ok=True)
timestamp = datetime.now().strftime("%y%m%d_%H%M")
pdf_path = f"screenshots/music_capture_{timestamp}.pdf"

# ✅ Chrome 옵션
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.set_page_load_timeout(30)


def remove_popups():
    """공통 팝업 제거"""
    js_scripts = [
        "document.querySelectorAll('iframe, .popup, .layer, .modal, .lyr_wrap, #popup, .dimmed, .window, .overlay').forEach(e=>e.remove());",
        "window.alert=function(){};window.confirm=function(){return true;};window.open=function(){return null;};"
    ]
    for s in js_scripts:
        try:
            driver.execute_script(s)
        except:
            pass


def capture_site(name, url, scroll_to=None, wait_selector=None, crop_height=None, extra_js=None):
    """사이트별 캡처"""
    print(f"[+] Capturing {name} ...")
    try:
        driver.get(url)
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        remove_popups()

        if extra_js:
            try:
                driver.execute_script(extra_js)
            except Exception as e:
                print(f"[!] JS 실행 오류 ({name}): {e}")

        if wait_selector:
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector)))
            except:
                pass

        if scroll_to:
            driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            time.sleep(2)

        # ✅ 스크린샷
        png_path = f"screenshots/{name}_{timestamp}.png"
        driver.save_screenshot(png_path)
        print(f"✅ {name} captured → {png_path}")

        if crop_height:
            img = Image.open(png_path)
            cropped = img.crop((0, 0, img.width, crop_height))
            cropped.save(png_path)

        return png_path

    except Exception as e:
        print(f"[!] {name} capture failed: {e}")
        return None


# ✅ 사이트별 맞춤 설정
sites = [
    # (사이트명, URL, 스크롤 위치, 대기 selector, crop 높이, 추가 JS)
    # ----------------------------
    # 🎵 멜론: 메인 최신앨범 영역
    ("melon",
     "https://www.melon.com/index.htm",
     1300,
     "div.wrap_chart_home",
     850,
     "document.querySelectorAll('#d_spop, #pop_notice, .popup_wrap').forEach(e=>e.remove());"),

    # 🎧 지니: '최신 앨범' 페이지 직접 진입
    ("genie",
     "https://www.genie.co.kr/newest/album",
     0,
     ".newest-list",
     950,
     """
     const albums = document.querySelector('.newest-list');
     if(albums) albums.scrollIntoView({behavior:'auto', block:'center'});
     """),

    # 🎼 벅스: '최신 앨범' 목록
    ("bugs",
     "https://music.bugs.co.kr/newest/album",
     300,
     ".albumList",
     950,
     """
     const el = document.querySelector('.albumList');
     if(el) el.scrollIntoView({behavior:'auto', block:'center'});
     """),

    # 💿 FLO: 오늘 발매 음악 (로그인 팝업 제거 + 스크롤)
    ("flo",
     "https://www.music-flo.com/browse/new-release",
     200,
     ".album-list",
     1100,
     """
     document.querySelectorAll('.popup, .modal, .dimmed, .login-popup, .notice-layer').forEach(e=>e.remove());
     window.scrollTo(0, 400);
     """),
]

images = []
for name, url, scroll_to, selector, crop, js in sites:
    img = capture_site(name, url, scroll_to=scroll_to, wait_selector=selector, crop_height=crop, extra_js=js)
    if img:
        images.append(img)

driver.quit()


# ✅ PDF 생성
if images:
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont("STSong-Light", 10)

    for img_path in images:
        img = Image.open(img_path)
        img_width, img_height = img.size
        scale = min(width / img_width, height / img_height)
        new_width = img_width * scale
        new_height = img_height * scale
        x = (width - new_width) / 2
        y = (height - new_height) / 2
        c.drawImage(ImageReader(img), x, y, new_width, new_height)
        c.showPage()

    c.save()
    print(f"📄 PDF created: {pdf_path}")

    for img_path in images:
        os.remove(img_path)
    print("🧹 PNG files removed.")
else:
    print("⚠️ No screenshots captured.")
