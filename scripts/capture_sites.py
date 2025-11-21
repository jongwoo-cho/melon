import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


# ==============================
#  공통 설정
# ==============================
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
timestamp = now.strftime("%Y%m%d_%H%M%S")

output_folder = "capture_output"
os.makedirs(output_folder, exist_ok=True)

flo_path   = os.path.join(output_folder, f"flo_{timestamp}.png")
melon_path = os.path.join(output_folder, f"melon_{timestamp}.png")
genie_path = os.path.join(output_folder, f"genie_{timestamp}.png")
bugs_path  = os.path.join(output_folder, f"bugs_{timestamp}.png")


# ==============================
#  크롬 옵션
# ==============================
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,5000")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)



# ==============================
#  사이트별 처리 함수
# ==============================

# --------------------------------------------------
#  FLO
# --------------------------------------------------
def handle_flo():
    url = "https://www.music-flo.com/"
    driver.get(url)
    time.sleep(2)

    # ----- 기존 팝업 제거 유지 -----
    try:
        driver.execute_script("""
            let sel = [
                '.popup', '.pop', '.modal', '.layer', '.event-popup',
                '[class*="Popup"]', '[id*="popup"]', '.cookie', '.cookie-popup'
            ];
            sel.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        """)
    except:
        pass
    time.sleep(1)

    # ----- FLO 스크롤 (오늘 발매 음악 기준) -----
    try:
        header = driver.find_element(By.XPATH, "//h2[contains(text(),'오늘 발매')]")

        js_code = '''
            const h = arguments[0];

            // h2가 포함된 섹션(최상위 section 또는 div)
            let p = h;
            while (p && p.parentElement && p.tagName.toLowerCase() !== 'section') {
                p = p.parentElement;
            }
            if (!p) { p = h.parentElement; }

            const rect = p.getBoundingClientRect();
            const sectionTop = rect.top + window.scrollY;
            const sectionHeight = rect.height;

            // 섹션의 35% 위치까지 스크롤
            const target = sectionTop + sectionHeight * 0.35;
            window.scrollTo({ top: target });
        '''
        driver.execute_script(js_code, header)
        time.sleep(1.2)

    except Exception as e:
        print("FLO scroll fallback:", e)
        driver.execute_script("window.scrollTo(0, 1400)")
        time.sleep(1)

    # ----- 캡처 -----
    driver.save_screenshot(flo_path)
    print("[FLO 캡처 완료]", flo_path)




# --------------------------------------------------
#  MELON (변경 없음)
# --------------------------------------------------
def handle_melon():
    url = "https://www.melon.com/index.htm"
    driver.get(url)
    time.sleep(2)

    try:
        driver.execute_script("""
            let popup = document.querySelector('#gnb_banner');
            if (popup) popup.remove();
        """)
    except:
        pass
    time.sleep(1)

    driver.execute_script("window.scrollTo(0, 800)")
    time.sleep(1)
    driver.save_screenshot(melon_path)
    print("[MELON 캡처 완료]", melon_path)



# --------------------------------------------------
#  GENIE (변경 없음)
# --------------------------------------------------
def handle_genie():
    url = "https://www.genie.co.kr/"
    driver.get(url)
    time.sleep(2)

    driver.execute_script("window.scrollTo(0, 900)")
    time.sleep(1)
    driver.save_screenshot(genie_path)
    print("[GENIE 캡처 완료]", genie_path)



# --------------------------------------------------
#  BUGS (팝업 제거 강화 유지)
# --------------------------------------------------
def handle_bugs():
    url = "https://music.bugs.co.kr/"
    driver.get(url)
    time.sleep(2)

    try:
        driver.execute_script("""
            document.querySelectorAll('.layerPopup, .modal, #popup, .popup').forEach(e => e.remove());
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        """)
    except:
        pass
    time.sleep(1)

    driver.execute_script("window.scrollTo(0, 900)")
    time.sleep(1)
    driver.save_screenshot(bugs_path)
    print("[BUGS 캡처 완료]", bugs_path)



# ==============================
#  실행
# ==============================
handle_flo()
handle_melon()
handle_genie()
handle_bugs()

driver.quit()

print("\n=== 전체 캡처 완료 ===")
