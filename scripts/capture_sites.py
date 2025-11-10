import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === 기본 설정 ===
SAVE_DIR = "screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

KST = pytz.timezone("Asia/Seoul")
timestamp = datetime.now(KST).strftime("%y%m%d_%H%M")

SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
}

# === 브라우저 옵션 ===
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")

driver = webdriver.Chrome(options=options)


def remove_popups():
    js = """
    let els = document.querySelectorAll('div, iframe, section');
    for (let el of els) {
        const z = parseInt(window.getComputedStyle(el).zIndex) || 0;
        if (z > 1000 || el.id.toLowerCase().includes('popup') || el.className.toLowerCase().includes('popup')) {
            el.style.display = 'none';
        }
    }
    // 쿠키 배너 제거
    let cookieEls = document.querySelectorAll("[id*='cookie'], [class*='cookie'], [class*='consent']");
    for (let el of cookieEls) el.style.display = 'none';
    """
    try:
        driver.execute_script(js)
    except Exception:
        pass


def capture_site(name, url):
    print(f"[+] Capturing {name} ...")
    driver.get(url)

    # 기본 대기: body 로딩
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except:
        print(f"[!] {name}: body load timeout")

    time.sleep(5)  # JS 완전 실행 대기
    remove_popups()
    time.sleep(2)

    filename = os.path.join(SAVE_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(filename)
    print(f"✅ {name} captured → {filename}")


# === 메인 루프 ===
for site, link in SITES.items():
    try:
        capture_site(site, link)
    except Exception as e:
        print(f"[❌] {site} failed: {e}")

driver.quit()
print("🎉 All captures complete.")
