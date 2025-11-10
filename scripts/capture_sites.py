import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
}


def setup_driver():
    options = Options()
    # GUI 모드 (headless 제거)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def remove_popups(driver):
    """공통 팝업 제거"""
    js_code = """
    const popups = document.querySelectorAll('div[role="dialog"], iframe, .popup, .layer_popup, .modal, .dimmed');
    popups.forEach(el => el.remove());
    """
    try:
        driver.execute_script(js_code)
    except Exception:
        pass


def scroll_full_page(driver):
    """스크롤 끝까지 내려서 lazy-load 포함 전체 로드"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    driver.execute_script("window.scrollTo(0, 0);")  # 다시 맨 위로


def capture_site(driver, name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(5)
    remove_popups(driver)
    scroll_full_page(driver)  # ⬅️ 페이지 끝까지 로드

    # 전체 높이 다시 계산
    full_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, full_height)
    time.sleep(0.5)

    path = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(path)
    print(f"✅ {name} captured → {path}")
    return path


def merge_to_pdf(images, output_path):
    pdf = FPDF()
    for img_path in images:
        img = Image.open(img_path)
        w, h = img.size
        ratio = min(210 / w * 96 / 25.4, 297 / h * 96 / 25.4)
        new_w, new_h = w * ratio, h * ratio
        pdf.add_page()
        temp = img_path.replace(".png", "_temp.jpg")
        img.convert("RGB").save(temp)
        pdf.image(temp, x=0, y=0, w=new_w, h=new_h)
        os.remove(temp)
    pdf.output(output_path, "F")
    print(f"📄 PDF saved → {output_path}")


def main():
    driver = setup_driver()
    captured = []

    for name, url in SITES.items():
        try:
            captured.append(capture_site(driver, name, url))
        except Exception as e:
            print(f"[!] {name} failed: {e}")

    driver.quit()

    if captured:
        pdf_path = os.path.join(SAVE_DIR, f"music_sites_{timestamp}.pdf")
        merge_to_pdf(captured, pdf_path)
        for f in captured:
            os.remove(f)
        print("🧹 PNGs deleted")


if __name__ == "__main__":
    main()
