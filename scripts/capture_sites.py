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

# 출력 폴더
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 현재 시각 (KST)
KST = pytz.timezone("Asia/Seoul")
timestamp = datetime.datetime.now(KST).strftime("%y%m%d_%H%M")

# 사이트 목록
SITES = {
    "melon": "https://www.melon.com/chart/index.htm",
    "genie": "https://www.genie.co.kr/chart/top200",
    "bugs": "https://music.bugs.co.kr/chart",
    "flo": "https://www.music-flo.com/"
}

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--lang=ko-KR")
    chrome_options.add_argument("--font-render-hinting=none")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.popups": 0,
        "intl.accept_languages": "ko-KR,ko,en-US,en"
    })

    # 웹드라이버 설치
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

def remove_popups(driver, site):
    """사이트별 팝업 및 레이어 제거"""
    try:
        driver.execute_script("""
            window.alert = function(){};
            window.confirm = function(){return true;};
            window.prompt = function(){return null;};
            window.open = function(){return null;};
        """)
    except:
        pass

    # 멜론: 팝업 div, 광고 레이어 제거
    if site == "melon":
        selectors = ["#popNotice", ".layer_popup", "#d_layer", ".wrap_popup", ".bg_dimmed", "#gnb_menu"]
    elif site == "genie":
        selectors = [".popup", ".lay_dim", "#app div[role='dialog']", "iframe", ".layer"]
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

def capture_site(driver, name, url):
    print(f"[+] {name} 캡처 중...")
    driver.get(url)
    time.sleep(5)
    remove_popups(driver, name)
    time.sleep(1)

    # 멜론은 상단 영역만
    if name == "melon":
        driver.execute_script("window.scrollTo(0, 0);")
        file_path = f"{OUTPUT_DIR}/{name}_{timestamp}.png"
        driver.get_screenshot_as_file(file_path)
        print(f"✅ {name} 캡처 완료 (상단 영역) → {file_path}")
        return file_path

    # FLO는 오늘 발매 음악 10개 영역까지 보이게
    if name == "flo":
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
            time.sleep(2)
        except:
            pass

    # 전체화면 캡처
    file_path = f"{OUTPUT_DIR}/{name}_{timestamp}.png"
    driver.save_screenshot(file_path)
    print(f"✅ {name} 캡처 완료 → {file_path}")
    return file_path

def create_pdf(images, timestamp):
    """캡처된 PNG → 하나의 PDF로 합치기"""
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

        # PNG 파일 정리
        for f in captured:
            os.remove(f)
        print("🧹 PNG 파일 삭제 완료")

    except Exception as e:
        driver.quit()
        print(f"❌ 오류 발생: {e}")
