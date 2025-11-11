import os
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

KST = pytz.timezone("Asia/Seoul")
timestamp = datetime.datetime.now(KST).strftime("%y%m%d_%H%M")

# 🔹 메인 페이지 기준 (홈)
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--lang=ko-KR")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.popups": 0,
        "intl.accept_languages": "ko-KR,ko,en-US,en"
    })

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def remove_popups(driver, site):
    """사이트별 팝업/레이어 제거"""
    try:
        driver.execute_script("""
            window.alert = function(){};
            window.confirm = function(){return true;};
            window.prompt = function(){return null;};
            window.open = function(){return null;};
        """)
    except:
        pass

    selectors = []
    if site == "melon":
        selectors = ["#popNotice", ".layer_popup", "#d_layer", ".wrap_popup", ".bg_dimmed", "iframe"]
    elif site == "genie":
        selectors = [".popup", ".lay_dim", ".layer", "iframe"]
    elif site == "bugs":
        selectors = [".layer", ".popup", "#popLayer", ".modal", "iframe"]
    elif site == "flo":
        selectors = [".modal", ".popup", ".popupContainer", "iframe"]

    for s in selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, s)
            for e in elems:
                driver.execute_script("arguments[0].remove();", e)
        except:
            continue
    time.sleep(1)


def scroll_to_latest_section(driver, site):
    """사이트별 ‘최신 앨범/오늘 발매 음악’ 섹션으로 스크롤"""
    if site == "melon":
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
    elif site == "genie":
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
    elif site == "bugs":
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.25);")
    elif site == "flo":
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4);")
    time.sleep(2)


def capture_site(driver, name, url):
    print(f"[+] {name} 캡처 중...")
    driver.get(url)
    time.sleep(6)

    remove_popups(driver, name)
    scroll_to_latest_section(driver, name)

    file_path = f"{OUTPUT_DIR}/{name}_{timestamp}.png"
    driver.save_screenshot(file_path)
    print(f"✅ {name} 캡처 완료 → {file_path}")
    return file_path


def create_pdf(images, timestamp):
    pdf_path = f"{OUTPUT_DIR}/captures_{timestamp}.pdf"
    pdf = FPDF()
    for img in images:
        pdf.add_page()
        pdf.image(img, 0, 0, 210, 0)
    pdf.output(pdf_path, "F")
    print(f"📄 PDF 생성 완료 → {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    driver = get_driver()
    captured = []

    try:
        for name, url in SITES.items():
            captured.append(capture_site(driver, name, url))

        driver.quit()
        pdf = create_pdf(captured, timestamp)

        # PNG 자동 삭제
        for f in captured:
            os.remove(f)
        print("🧹 PNG 파일 삭제 완료")

    except Exception as e:
        driver.quit()
        print(f"❌ 오류 발생: {e}")
