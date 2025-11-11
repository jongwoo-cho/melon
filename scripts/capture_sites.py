import os
import time
from datetime import datetime, timedelta
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
from fpdf import FPDF

SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "flo": "https://www.music-flo.com/",
}

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def brutal_popup_remover(driver):
    js = """
        // 멜론 팝업
        const melonPop = document.querySelector('#d_pop, #popNotice, #gnb_menu_wrap');
        if (melonPop) melonPop.remove();

        // 지니 팝업
        const geniePop = document.querySelector('.popup-wrap, .layer-popup, #popup');
        if (geniePop) geniePop.remove();

        // FLO 팝업
        const floPop = document.querySelector('.modal-container, .popup, .MuiDialog-root');
        if (floPop) floPop.remove();

        // 오버레이 및 모달 전부 제거
        const overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [id*="popup"], [role="dialog"]');
        overlays.forEach(el => el.remove());

        // 스크롤 및 가시성 방해 제거
        document.body.style.overflow = 'auto';
        document.body.style.position = 'relative';
    """
    try:
        driver.execute_script(js)
        time.sleep(0.5)
        # 혹시 alert() 뜨면 자동 닫기
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
        except:
            pass
    except Exception as e:
        print(f"[!] popup 제거 실패: {e}")

def capture_full_page(driver, name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)
    time.sleep(4)
    brutal_popup_remover(driver)
    time.sleep(1.5)

    # FLO의 경우 오늘 발매 음악 보이도록 스크롤
    if name == "flo":
        try:
            target = driver.find_element(By.CSS_SELECTOR, "section[data-testid='newReleaseTodaySection']")
            for _ in range(8):
                driver.execute_script("arguments[0].scrollTop += 400;", target)
                time.sleep(0.5)
        except Exception:
            pass

    # 전체 높이 계산 후 캡처
    full_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, full_height)
    time.sleep(2)
    timestamp = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%y%m%d_%H%M")
    path = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(path)
    print(f"✅ {name} captured → {path}")
    return path

def merge_to_pdf(images, output_path):
    pdf = FPDF()
    for img in images:
        if not os.path.exists(img):
            continue
        image = Image.open(img)
        w, h = image.size
        ratio = min(210 / (w * 0.2645), 297 / (h * 0.2645))
        new_w, new_h = w * 0.2645 * ratio, h * 0.2645 * ratio
        pdf.add_page()
        temp = img.replace(".png", "_tmp.jpg")
        image.convert("RGB").save(temp)
        pdf.image(temp, x=0, y=0, w=new_w, h=new_h)
        os.remove(temp)
    pdf.output(output_path, "F")
    print(f"📄 PDF saved → {output_path}")

def main():
    driver = setup_driver()
    captured = []
    for name, url in SITES.items():
        try:
            captured.append(capture_full_page(driver, name, url))
        except Exception as e:
            print(f"[!] {name} 실패: {e}")
    driver.quit()

    timestamp = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%y%m%d_%H%M")
    pdf_path = os.path.join(SAVE_DIR, f"music_sites_{timestamp}.pdf")
    merge_to_pdf(captured, pdf_path)

if __name__ == "__main__":
    main()
