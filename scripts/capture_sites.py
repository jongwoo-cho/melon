import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from fpdf import FPDF

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

# KST 기준 timestamp
timestamp = datetime.now().strftime("%y%m%d_%H%M")

# 사이트 목록
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "flo": "https://www.music-flo.com/",
}

def setup_driver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ko-KR")  # 지니 한글 깨짐 방지
    # headful Chrome 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def remove_popup(driver, site_name):
    """사이트별 팝업 제거"""
    try:
        if site_name == "melon":
            driver.execute_script("""
                const pop = document.querySelector('#d_pop');
                if(pop) pop.remove();
            """)
        elif site_name == "genie":
            driver.execute_script("""
                const pop = document.querySelector('.popup-wrap');
                if(pop) pop.remove();
            """)
        elif site_name == "flo":
            driver.execute_script("""
                const pop = document.querySelector('.modal-container');
                if(pop) pop.remove();
            """)
    except Exception as e:
        print(f"[!] {site_name} 팝업 제거 실패: {e}")

def capture_full_page(driver, name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(3)
    remove_popup(driver, name)
    time.sleep(1)

    if name == "flo":
        # 오늘 발매 음악 10개 이상 보이도록 스크롤
        try:
            content_area = driver.find_element(By.CSS_SELECTOR, "section[data-testid='newReleaseTodaySection']")
            for _ in range(10):
                driver.execute_script("arguments[0].scrollTop += 300;", content_area)
                time.sleep(0.5)
        except NoSuchElementException:
            pass

    # 전체 페이지 스크롤 캡처
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
    images = [Image.open(p) for p in screenshots if os.path.exists(p)]
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

def merge_to_pdf(images, output_path):
    pdf = FPDF()
    for img_path in images:
        if not os.path.exists(img_path):
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
    else:
        print("[!] 캡처된 이미지 없음. PDF 생성 생략")

if __name__ == "__main__":
    main()
