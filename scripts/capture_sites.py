import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# KST 시간
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
timestamp = now.strftime("%Y%m%d_%H%M%S")

# 폴더 설정
output_folder = "capture_output"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# -------------------------------------------------------
#  Chrome 옵션 (헤드리스 환경 완전 대응)
# -------------------------------------------------------
options = webdriver.ChromeOptions()

# Headless 안정화 필수 옵션
options.add_argument("--headless=new")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")

# 기존 옵션 그대로 유지
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-notifications")
options.add_argument("--disable-gpu")

# Headless 환경에서는 window-size 필수
options.add_argument("--window-size=1920,5000")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# -------------------------------------------------------
#  공통 캡처 함수
# -------------------------------------------------------
def full_screenshot(filename):
    screenshot_path = os.path.join(output_folder, filename)
    driver.save_screenshot(screenshot_path)
    return screenshot_path


# -------------------------------------------------------
#  FLO 처리 — 섹션 정확 스크롤 + 팝업 제거 유지
# -------------------------------------------------------
def process_flo():
    print("\n[FLO] 접속…")
    driver.get("https://www.music-flo.com")
    time.sleep(3)

    # 기존 팝업 제거 유지
    try:
        close_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-close, .close-btn, .btn-close"))
        )
        close_btn.click()
        time.sleep(1)
    except:
        pass

    print("[FLO] '오늘 발매 음악' 요소 탐색…")

    try:
        today_release_header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h2[contains(text(), '오늘 발매')]")
            )
        )

        # 요소 y 좌표 가져오기
        y_pos = driver.execute_script(
            "return arguments[0].getBoundingClientRect().top + window.pageYOffset;",
            today_release_header
        )

        target_y = max(y_pos - 200, 0)

        driver.execute_script(f"window.scrollTo({{ top: {target_y}, behavior: 'instant' }});")
        time.sleep(2)

    except Exception as e:
        print("FLO 스크롤 실패:", e)

    fname = f"flo_capture_{timestamp}.png"
    full_screenshot(fname)
    return fname


# -------------------------------------------------------
# 다른 사이트는 전부 기존 로직 그대로 유지
# -------------------------------------------------------
def process_melon():
    driver.get("https://www.melon.com")
    time.sleep(3)
    fname = f"melon_capture_{timestamp}.png"
    full_screenshot(fname)
    return fname

def process_genie():
    driver.get("https://www.genie.co.kr")
    time.sleep(3)
    fname = f"genie_capture_{timestamp}.png"
    full_screenshot(fname)
    return fname

def process_bugs():
    driver.get("https://music.bugs.co.kr")
    time.sleep(3)
    fname = f"bugs_capture_{timestamp}.png"
    full_screenshot(fname)
    return fname


# -------------------------------------------------------
# 전체 실행
# -------------------------------------------------------
flo = process_flo()
melon = process_melon()
genie = process_genie()
bugs = process_bugs()

driver.quit()
print("\n=== 전체 캡처 완료 ===")
