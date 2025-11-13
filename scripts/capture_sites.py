import os, time
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

# ---- 설정 ----
os.makedirs("screenshots", exist_ok=True)
timestamp = datetime.now().strftime("%y%m%d_%H%M")
pdf_path = f"screenshots/music_capture_{timestamp}.pdf"

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")
chrome_options.add_argument("--font-render-hinting=none")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.set_page_load_timeout(30)

# ---- 팝업 제거 ----
def remove_popups():
    scripts = [
        "document.querySelectorAll('iframe, div[role=dialog], .popup, .modal, .lyr_wrap, .dimmed, #pop_notice, #d_spop').forEach(e=>e.remove());",
        "window.alert=function(){};window.confirm=function(){return true;};window.open=function(){return null;};",
        "document.body.style.overflow='auto';"
    ]
    for s in scripts:
        try:
            driver.execute_script(s)
        except:
            pass

# ---- 캡처 함수 ----
def capture_site(name, url, scroll_target=None, crop_height=800):
    print(f"[+] Capturing {name} ...")
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        remove_popups()

        if scroll_target:
            try:
                element = driver.find_element(By.CSS_SELECTOR, scroll_target)
                driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", element)
                time.sleep(2)
            except Exception:
                pass

        png_path = f"screenshots/{name}_{timestamp}.png"
        driver.save_screenshot(png_path)

        # 상단만 자르기
        img = Image.open(png_path)
        cropped = img.crop((0, 0, img.width, crop_height))
        cropped.save(png_path)
        return png_path
    except Exception as e:
        print(f"[!] {name} failed: {e}")
        return None

# ---- 사이트 목록 ----
sites = [
    ("melon", "https://www.melon.com/new/index.htm", "#conts_section", 900),
    ("genie", "https://www.genie.co.kr/", ".newest", 900),
    ("bugs", "https://music.bugs.co.kr/", "#container", 900),
    ("flo", "https://www.music-flo.com/", "main", 900),
]

images = []
for name, url, selector, crop in sites:
    img = capture_site(name, url, scroll_target=selector, crop_height=crop)
    if img:
        images.append(img)

driver.quit()

# ---- PDF 생성 ----
if images:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))  # ✅ 한글 폰트 등록

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    for img_path in images:
        img = Image.open(img_path)
        scale = min(width / img.width, height / img.height)
        new_width = img.width * scale
        new_height = img.height * scale
        x = (width - new_width) / 2
        y = (height - new_height) / 2
        c.drawImage(img_path, x, y, new_width, new_height)
        c.showPage()

    c.save()
    print(f"📄 PDF created: {pdf_path}")

    # PNG 정리
    for img_path in images:
        os.remove(img_path)
else:
    print("⚠️ No screenshots captured.")
