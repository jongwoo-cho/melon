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

# 스크린샷 저장 폴더
SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

# KST 기준 시각
kst = pytz.timezone("Asia/Seoul")
now = datetime.now(kst)
timestamp = now.strftime("%y%m%d_%H%M")

# 캡처 대상 사이트
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
}

def setup_driver():
    """Chrome 드라이버 설정 (GUI 모드, 팝업 제거 옵션 포함)"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def remove_popups(driver):
    """사이트 공통 팝업 제거 (광고, 알림, 배너 등)"""
    js_code = """
    const popups = document.querySelectorAll('div[role="dialog"], iframe, .popup, .layer_popup, .modal, .dimmed');
    popups.forEach(el => el.remove());
    const overlays = document.querySelectorAll('*');
    overlays.forEach(el => {
        if (getComputedStyle(el).zIndex > 1000) el.remove();
    });
    """
    try:
        driver.execute_script(js_code)
    except Exception:
        pass


def capture_site(driver, name, url):
    """사이트 캡처"""
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(5)
    remove_popups(driver)
    time.sleep(1)

    # 전체 페이지 스크롤 높이 계산
    full_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, 1080)")
    driver.set_window_size(1920, full_height)
    time.sleep(1)

    # PNG 파일 저장
    img_path = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(img_path)
    print(f"✅ {name} captured → {img_path}")
    return img_path


def merge_to_pdf(image_files, output_path):
    """여러 PNG를 하나의 PDF로 합침"""
    pdf = FPDF()
    for img_path in image_files:
        img = Image.open(img_path)
        w, h = img.size
        pdf_w, pdf_h = 210, 297  # A4 기준(mm)
        ratio = min(pdf_w / w * 96 / 25.4, pdf_h / h * 96 / 25.4)
        new_w, new_h = w * ratio, h * ratio
        pdf.add_page()
        temp_jpg = img_path.replace(".png", "_temp.jpg")
        img.convert("RGB").save(temp_jpg)
        pdf.image(temp_jpg, x=0, y=0, w=new_w, h=new_h)
        os.remove(temp_jpg)
    pdf.output(output_path, "F")
    print(f"📄 Combined PDF saved → {output_path}")


def main():
    driver = setup_driver()
    captured_images = []

    for name, url in SITES.items():
        try:
            img_path = capture_site(driver, name, url)
            captured_images.append(img_path)
        except Exception as e:
            print(f"[!] {name} capture failed: {e}")
            continue

    driver.quit()

    if captured_images:
        pdf_path = os.path.join(SAVE_DIR, f"music_sites_{timestamp}.pdf")
        merge_to_pdf(captured_images, pdf_path)

        # PNG 파일은 정리
        for img in captured_images:
            os.remove(img)
        print("🧹 Temporary PNGs removed")

if __name__ == "__main__":
    main()
