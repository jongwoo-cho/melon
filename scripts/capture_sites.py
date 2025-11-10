import os
import time
import pytz
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === 브라우저 설정 ===
def get_driver():
    options = Options()
    # headless 제거! (Xvfb로 가상 화면 사용)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(40)
    return driver


# === 팝업 제거 함수 ===
def remove_popups(driver):
    """공통 팝업 제거"""
    js = """
    const removeEls = [
        'iframe', 'div[role="dialog"]', 'div[id*="popup"]', 
        'div[class*="popup"]', 'div[class*="layer"]', 'div[class*="modal"]',
        'div[id*="dimmed"]', '#dimmedLayer', '#appLayer'
    ];
    removeEls.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => el.remove());
    });
    """
    try:
        driver.execute_script(js)
    except Exception:
        pass


# === 전체 페이지 캡처 ===
def capture_full_page(name, url):
    driver = get_driver()
    print(f"[+] Capturing {name} ...")

    try:
        driver.get(url)
        time.sleep(5)

        # 팝업 제거 반복 시도
        for _ in range(5):
            remove_popups(driver)
            time.sleep(1)

        # 페이지 로딩 대기 (메인 콘텐츠 보이기)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            print(f"[!] {name}: main content load timeout")

        # 페이지 높이 계산 (documentElement 기준)
        full_height = driver.execute_script("""
            return Math.max(
                document.body ? document.body.scrollHeight : 0,
                document.documentElement ? document.documentElement.scrollHeight : 0,
                1080
            );
        """)

        driver.set_window_size(1920, full_height)
        time.sleep(2)

        # === KST 기준 파일명 생성 ===
        kst = pytz.timezone("Asia/Seoul")
        timestamp = datetime.now(kst).strftime("%y%m%d_%H%M")

        os.makedirs("screenshots", exist_ok=True)
        screenshot_path = f"screenshots/{name}_{timestamp}.png"

        driver.save_screenshot(screenshot_path)
        print(f"✅ {name} captured → {screenshot_path}")

    except Exception as e:
        print(f"[X] {name} capture failed: {e}")

    finally:
        driver.quit()


# === 실행 섹션 ===
if __name__ == "__main__":
    sites = {
        "melon": "https://www.melon.com/chart/index.htm",
        "genie": "https://www.genie.co.kr/chart/top200",
        "bugs": "https://music.bugs.co.kr/chart",
        "flo": "https://www.music-flo.com/",
    }

    for name, url in sites.items():
        capture_full_page(name, url)
