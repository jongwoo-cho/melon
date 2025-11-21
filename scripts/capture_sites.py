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
from selenium.webdriver.common.keys import Keys
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

# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-notifications")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# -------------------------------------------------------
#  공통 캡처 함수 (기존 로직 그대로 유지)
# -------------------------------------------------------
def full_screenshot(filename):
    screenshot_path = os.path.join(output_folder, filename)
    driver.save_screenshot(screenshot_path)
    return screenshot_path


# -------------------------------------------------------
#  FLO 처리 — 팝업 제거는 그대로 유지 + ‘오늘 발매 음악’ 기준 스크롤 확실히 수행
# -------------------------------------------------------
def process_flo():
    print("\n[FLO] 페이지 접속 중…")
    driver.get("https://www.music-flo.com")
    time.sleep(3)

    # ⬇ FLO 팝업 제거 로직 (기존 유지)
    try:
        close_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-close, .close-btn, .btn-close"))
        )
        close_btn.click()
        time.sleep(1)
    except:
        pass  # 팝업 없어도 무시

    print("[FLO] '오늘 발매 음악' 섹션 위치 탐색…")

    # ⬇ '오늘 발매 음악' 텍스트가 있는 h2 요소 직접 찾기 (정확하게 동작함)
    try:
        today_release_header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), '오늘 발매')]"))
        )

        # 요소의 y 좌표 값을 구하기
        y_pos = driver.execute_script(
            "return arguments[0].getBoundingClientRect().top + window.pageYOffset;", 
            today_release_header
        )

        # 요소가 화면 중앙에 오도록 약간 위쪽에서 멈춤
        target_y = max(y_pos - 200, 0)

        driver.execute_script(f"window.scrollTo({{ top: {target_y}, behavior: 'smooth' }});")
        time.sleep(2)

    except Exception as e:
        print("FLO 스크롤 실패: ", e)

    # 캡처
    flo_file = f"flo_capture_{timestamp}.png"
    full_screenshot(flo_file)

    print("[FLO] 캡처 완료 →", flo_file)
    return flo_file


# -------------------------------------------------------
#  다른 사이트 로직은 전부 기존 그대로 유지
# -------------------------------------------------------

def process_melon():
    driver.get("https://www.melon.com")
    time.sleep(3)
    melon_file = f"melon_capture_{timestamp}.png"
    full_screenshot(melon_file)
    return melon_file


def process_genie():
    driver.get("https://www.genie.co.kr")
    time.sleep(3)
    genie_file = f"genie_capture_{timestamp}.png"
    full_screenshot(genie_file)
    return genie_file


def process_bugs():
    driver.get("https://music.bugs.co.kr")
    time.sleep(3)
    bugs_file = f"bugs_capture_{timestamp}.png"
    full_screenshot(bugs_file)
    return bugs_file


# -------------------------------------------------------
#  전체 실행
# -------------------------------------------------------

flo_img = process_flo()
melon_img = process_melon()
genie_img = process_genie()
bugs_img = process_bugs()

driver.quit()

print("\n=== 전체 캡처 완료 ===")
