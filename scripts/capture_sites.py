import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from fpdf import FPDF

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
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--font-render-hinting=none")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def remove_popups(driver):
    """공통 팝업 제거 및 반복 제거"""
    js_code = """
    function removeAllPopups() {
        const els = document.querySelectorAll(
            'iframe, .popup, .layer_popup, .modal, .dimmed, [role="dialog"], #popLayer'
        );
        els.forEach(e => e.remove());
    }
    removeAllPopups();
    setTimeout(removeAllPopups, 1000);
    setTimeout(removeAllPopups, 2000);
    """
    try:
        driver.execute_script(js_code)
    except:
        pass

def capture_full_page_scroll(driver, name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(3)
    remove_popups(driver)
    time.sleep(1)
    remove_popups(driver)
    time.sleep(1)

    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")
    screenshots = []
    scroll_position = 0
    part = 1

    while scroll_position < total_height:
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(1.5)
        path = os.path.join(SAVE_DIR, f"{name}_part{part}.png")
        driver.save_screenshot(path)
        screenshots.append(path)
        scroll_position += viewport_height - 200  # 약간의 overlap
        part += 1
        total_height = driver.execute_script("return document.body.scrollHeight")
        if scroll_position >= total_height:
            break

    # 이미지 병합
    images = [Image.open(p) for p in screenshots]
    widths, heights = zip(*(i.size for i in images))
    total_height = sum(heights) - (len(images) - 1) * 200
    merged = Image.new("RGB", (widths[0], total_height))
    y = 0
    for i, img in enumerate(images):
        if i > 0:
            y -= 200
        merged.paste(img, (0, y))
        y += img.height
    for p in screenshots:
        os.remove(p)

    out_path = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
    merged.save(out_path)
    print(f"✅ {name} captured → {out_path}")
    return out_path

def merge_to_pdf(images, output_path):
    pdf = FPDF()
    for img_path in images:
        img = Image.open(img_path)
        w, h = img.size
        ratio = min(210 / (w * 0.2645), 297 / (h * 0.2645))
        new_w, new_h = w * 0.2645 * ratio, h * 0.2645 * ratio
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
            captured.append(capture_full_page_scroll(driver, name, url))
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
