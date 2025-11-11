import os
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF

# 저장 폴더 설정
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 타임스탬프 (한국 시간)
KST = pytz.timezone("Asia/Seoul")
timestamp = datetime.datetime.now(KST).strftime("%y%m%d_%H%M")

# 사이트 목록
SITES = {
    "melon": "https://www.melon.com/chart/index.htm",
    "genie": "https://www.genie.co.kr/chart/top200",
    "bugs": "https://music.bugs.co.kr/chart",
    "flo": "https://www.music-flo.com/"
}

# Chrome 옵션
def get_chrome():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 0,
        "profile.managed_default_content_settings.popups": 0,
        "profile.managed_default_content_settings.javascript": 1
    })

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

# 팝업 제거
def remove_popups(driver, site):
    try:
        # 자바스크립트 alert/confirm 차단
        driver.execute_script("""
            window.alert = function(){};
            window.confirm = function(){return true;};
            window.prompt = function(){return null;};
            window.open = function(){return null;};
        """)
    except:
        pass

    time.sleep(1)

    # 사이트별 팝업 제거
    try:
        if site == "melon":
            for sel in ["#popNotice", ".layer_popup", "#d_layer"]:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    driver.execute_script("arguments[0].remove();", e)

        elif site == "genie":
            for sel in [".popup", ".lay_dim", "#app div[role='dialog']", "iframe"]:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    driver.execute_script("arguments[0].remove();", e)

        elif site == "bugs":
            for sel in [".layer", ".popup", "#popLayer", ".modal", "iframe"]:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    driver.execute_script("arguments[0].remove();", e)

        elif site == "flo":
            for sel in [".modal", ".popup", ".popupContainer", "iframe"]:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    driver.execute_script("arguments[0].remove();", e)
    except Exception as e:
        print(f"[{site}] 팝업 제거 중 오류: {e}")

# 사이트 전체 캡처
def capture_site(name, url, driver):
    print(f"[+] {name} 캡처 시작...")
    driver.get(url)
    time.sleep(5)
    remove_popups(driver, name)
    time.sleep(1)

    if name == "flo":
        # FLO 오늘 발매 음악 10개 보이게 스크롤
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
            time.sleep(3)
        except:
            pass

    file_path = f"{OUTPUT_DIR}/{name}_{timestamp}.png"
    driver.save_screenshot(file_path)
    print(f"✅ {name} 캡처 완료 → {file_path}")
    return file_path

# PDF로 병합
def create_pdf(images, timestamp):
    pdf_path = f"{OUTPUT_DIR}/captures_{timestamp}.pdf"
    pdf = FPDF()
    for img in images:
        pdf.add_page()
        pdf.image(img, 0, 0, 210, 0)  # A4 폭 기준
    pdf.output(pdf_path, "F")
    print(f"📄 PDF 생성 완료 → {pdf_path}")
    return pdf_path

# 메인 실행
if __name__ == "__main__":
    driver = get_chrome()
    captured = []

    try:
        for name, url in SITES.items():
            captured.append(capture_site(name, url, driver))

        driver.quit()

        pdf = create_pdf(captured, timestamp)

        # PNG 삭제
        for f in captured:
            os.remove(f)
        print("🧹 PNG 파일 삭제 완료")

    except Exception as e:
        driver.quit()
        print(f"❌ 오류 발생: {e}")
