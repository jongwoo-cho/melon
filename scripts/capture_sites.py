import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from fpdf import FPDF

# -----------------------------
# 저장 경로
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "../screenshots")
os.makedirs(SAVE_DIR, exist_ok=True)

# -----------------------------
# 사이트 목록
# -----------------------------
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
}

# -----------------------------
# 드라이버 설정
# -----------------------------
def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# -----------------------------
# 팝업 제거 (공통)
# -----------------------------
def remove_popups(driver):
    js = """
        const selectors = [
            '#d_pop', '#popNotice', '#autoplay_layer',
            '.layer-popup', '.popup', '.modal', '.overlay', '.dimmed',
            '.modal-container', '.popup-wrap', '#popup', '.MuiDialog-root'
        ];
        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(e => e.remove());
        });
        document.body.style.overflow = 'auto';
        document.body.style.position = 'relative';
    """
    try:
        driver.execute_script(js)
        time.sleep(0.5)
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
        except:
            pass
    except:
        pass

# -----------------------------
# 사이트별 캡처
# -----------------------------
def capture_site(driver, name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(4)
    remove_popups(driver)

    # FLO: 오늘 발매 음악 10개 영역 스크롤
    if name == "flo":
        try:
            section = driver.find_element(By.CSS_SELECTOR, "section[data-testid='newReleaseTodaySection']")
            for _ in range(6):
                driver.execute_script("arguments[0].scrollTop += 400;", section)
                time.sleep(0.3)
        except:
            pass

    # 전체 높이 계산 후 스크린샷
    full_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, full_height)
    time.sleep(1)

    timestamp = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%y%m%d_%H%M")
    path = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(path)
    print(f"✅ {name} captured → {path}")
    return path

# -----------------------------
# PNG → PDF 변환
# -----------------------------
def make_pdf(image_list):
    pdf = FPDF()
    for img in image_list:
        if not os.path.exists(img):
            continue
        im = Image.open(img)
        w, h = im.size
        ratio = min(210 / (w * 0.2645), 297 / (h * 0.2645))
        new_w, new_h = w * 0.2645 * ratio, h * 0.2645 * ratio
        pdf.add_page()
        temp_jpg = img.replace(".png", "_temp.jpg")
        im.convert("RGB").save(temp_jpg)
        pdf.image(temp_jpg, x=0, y=0, w=new_w, h=new_h)
        os.remove(temp_jpg)
    timestamp = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%y%m%d_%H%M")
    pdf_path = os.path.join(SAVE_DIR, f"music_sites_{timestamp}.pdf")
    pdf.output(pdf_path, "F")
    print(f"📄 PDF saved → {pdf_path}")

# -----------------------------
# 메인 실행
# -----------------------------
def main():
    driver = setup_driver()
    captured = []
    for name, url in SITES.items():
        try:
            captured.append(capture_site(driver, name, url))
        except Exception as e:
            print(f"[!] {name} 실패: {e}")
    driver.quit()
    make_pdf(captured)

if __name__ == "__main__":
    main()
