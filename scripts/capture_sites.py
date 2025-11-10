import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from fpdf import FPDF

# 저장 폴더
SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

# 시간 설정 (KST)
kst = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

# 사이트 목록
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
}

def setup_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--disable-gpu")
    # 크롬 팝업/알림 차단
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2,
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def capture_full_page(driver, name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(3)

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
        scroll_position += viewport_height - 200
        part += 1
        total_height = driver.execute_script("return document.body.scrollHeight")
        if scroll_position >= total_height:
            break

    # PNG 병합
    try:
        images = [Image.open(p) for p in screenshots if os.path.exists(p)]
        if not images:
            print(f"[!] {name} 스크린샷이 존재하지 않아 PDF를 생성할 수 없습니다.")
            return None
        widths, heights = zip(*(i.size for i in images))
        merged_height = sum(heights) - (len(images)-1)*200
        merged = Image.new("RGB", (widths[0], merged_height))
        y = 0
        for i, img in enumerate(images):
            if i > 0: y -= 200
            merged.paste(img, (0, y))
            y += img.height
        out_path = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
        merged.save(out_path)
        for p in screenshots: os.remove(p)
        print(f"✅ {name} captured → {out_path}")
        return out_path
    except Exception as e:
        print(f"[!] {name} 병합 오류: {e}")
        return None

def merge_to_pdf(images, output_path):
    try:
        pdf = FPDF()
        for img_path in images:
            if not img_path or not os.path.exists(img_path):
                continue
            img = Image.open(img_path)
            w, h = img.size
            ratio = min(210 / (w * 0.2645), 297 / (h * 0.2645))
            new_w, new_h = w * 0.2645 * ratio, h * 0.2645 * ratio
            pdf.add_page()
            temp = img_path.replace(".png","_temp.jpg")
            img.convert("RGB").save(temp)
            pdf.image(temp, x=0, y=0, w=new_w, h=new_h)
            os.remove(temp)
        pdf.output(output_path, "F")
        print(f"📄 PDF saved → {output_path}")
    except Exception as e:
        print(f"[!] PDF 생성 실패: {e}")

def main():
    driver = setup_driver()
    captured = []
    for name, url in SITES.items():
        try:
            result = capture_full_page(driver, name, url)
            if result:
                captured.append(result)
        except Exception as e:
            print(f"[!] {name} 실패: {e}")
    driver.quit()

    if captured:
        pdf_path = os.path.join(SAVE_DIR, f"music_sites_{timestamp}.pdf")
        merge_to_pdf(captured, pdf_path)
        print("🧹 PNG 삭제 완료")
    else:
        print("[!] 캡처된 이미지 없음. PDF 생성 생략")

if __name__ == "__main__":
    main()
