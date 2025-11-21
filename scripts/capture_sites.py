import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from fpdf import FPDF
from PIL import Image

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

# KST 시간
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
timestamp = now.strftime("%y%m%d_%H%M")

# 저장 폴더
OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 사이트 정보
SITES = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/"
}

# Chrome 옵션
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")

driver = webdriver.Chrome(service=Service(), options=chrome_options)
wait = WebDriverWait(driver, 10)

captured_files = []


# -----------------------------------------------------------
# 벅스 팝업 제거 (그대로 유지)
# -----------------------------------------------------------
def remove_bugs_popups(driver, timeout=6.0):
    try:
        close_btn_selectors = [
            ".pop_close", ".btn_close", ".btn-close", ".close", ".layerClose",
            ".btnClose", ".lay-close", ".btnClosePop", ".pop_btn_close"
        ]
        for sel in close_btn_selectors:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in els:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", e)
                    e.click()
                except:
                    pass

        texts = ["닫기", "팝업닫기", "×", "✕", "Close", "close"]
        for t in texts:
            matches = driver.find_elements(By.XPATH, f"//*[text()[normalize-space()='{t}']]")
            for m in matches:
                try:
                    m.click()
                except:
                    try:
                        driver.execute_script("arguments[0].click();", m)
                    except:
                        pass

        try:
            body = driver.find_element(By.TAG_NAME, "body")
            for _ in range(3):
                body.send_keys(Keys.ESCAPE)
                time.sleep(0.2)
        except:
            pass

        js = r"""
        (function(timeout_ms){
            function removeNode(n){
                try{ if(n && n.parentNode) n.parentNode.removeChild(n); }catch(e){}
            }
            const selectors = [
                '#layPop','#layer_pop','#popup','#popupLayer','.layer-popup','.pop_layer','.popup',
                '.modal','.modal-bg','.modal-backdrop','.dimmed','.dimmedLayer','.popdim',
                '.ly_wrap','.ly_pop','.pop_wrap','.eventLayer','.evt_layer'
            ];

            function strongRemove(){
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => removeNode(el));
                });
                document.documentElement.style.overflow = 'auto';
                document.body.style.overflow = 'auto';
            }

            for (let i = 0; i < 5; i++) strongRemove();

            const interval = setInterval(strongRemove, 300);
            setTimeout(() => clearInterval(interval), timeout_ms);
        })(%d);
        """ % int(timeout * 1000)

        driver.execute_script(js)
        time.sleep(1)
        return True

    except:
        return False


# -----------------------------------------------------------
# FLO — ‘오늘 발매 음악’ 섹션 아래가 확실히 보이도록 스크롤
# -----------------------------------------------------------
def handle_flo(driver):
    # 기존 팝업 제거 유지
    try:
        driver.execute_script("""
            let sel = [
                '.popup', '.pop', '.modal', '.layer', '.event-popup',
                '[class*="Popup"]', '[id*="popup"]', '.cookie', '.cookie-popup'
            ];
            sel.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflo
