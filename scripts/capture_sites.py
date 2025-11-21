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
chrome_options.add_argument("--disable-dev-dev-shm-usage")
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

        # 강력한 JS 팝업 제거
        js = r"""
        (function(timeout_ms){
            function removeNode(n){
                try{ if(n && n.parentNode) n.parentNode.removeChild(n); }catch(e){}
            }
            function tryClick(el){
                try{ el.click(); }catch(e){
                    try{ el.dispatchEvent(new Event('click')); }catch(e){}
                }
            }
            const selectors = [
                '#layPop','#layer_pop','#popup','#popupLayer','.layer-popup','.pop_layer','.popup',
                '.modal','.modal-bg','.modal-backdrop','.dimmed','.dimmedLayer','.popdim',
                '.ly_wrap','.ly_pop','.pop_wrap','.eventLayer','.evt_layer'
            ];
            const texts = ['닫기','팝업닫기','Close','close','×','✕'];

            function strongRemove(){
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => removeNode(el));
                });

                document.querySelectorAll('[role="dialog"], [aria-modal="true"]').forEach(el => removeNode(el));

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

    except Exception as e:
        print("[!] remove_bugs_popups error:", e)
        return False


# -----------------------------------------------------------
# FLO — 캡처 영역 확실히 아래로 내리는 단일 확정 솔루션
# -----------------------------------------------------------
def handle_flo(driver):
    # 기존 팝업 제거 로직 그대로 유지
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
    time.sleep(0.8)

    # === 핵심: “오늘 발매 음악” 기준으로 아래로 스크롤 ===
    try:
        header = driver.find_element(By.XPATH, "//h2[contains(text(),'오늘 발매')]")

        driver.execute_script("""
            const h = arguments[0];
            const rect = h.getBoundingClientRect();
            const absoluteTop = rect.top + window.scrollY;

            // 섹션 아래를 확실하게 보여주기 위해 +400px
            window.scrollTo({
                top: absoluteTop + 400,
                behavior: 'instant'
            });
        """, header)

        time.sleep(1.0)

    except:
        # fallback
        driver.execute_script("window.scrollTo(0, 1200)")
        time.sleep(0.8)


# -----------------------------------------------------------
# 사이트별 캡처
# -----------------------------------------------------------
def capture_site(name, url):
    driver.get(url)
    time.sleep(5)

    if name == "flo":
        handle_flo(driver)

    elif name == "bugs":
        for _ in range(2):
            remove_bugs_popups(driver, timeout=3.0)
            time.sleep(0.5)

    else:
        try:
            driver.execute_script("""
                let elems = document.querySelectorAll('[class*="popup"], [id*="popup"], .dimmed, .overlay, .modal');
                elems.forEach(e => e.remove());
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
            """)
        except:
            pass

    time.sleep(1)
    screenshot_path = os.path.join(OUTPUT_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(screenshot_path)
    captured_files.append(screenshot_path)
    print(f"✅ {name} captured → {screenshot_path}")


# -----------------------------------------------------------
# 실행
# -----------------------------------------------------------
for site_name, site_url in SITES.items():
    capture_site(site_name, site_url)

driver.quit()

# -----------------------------------------------------------
# PNG → PDF 변환
# -----------------------------------------------------------
pdf_path = os.path.abspath(os.path.join(OUTPUT_DIR, f"music_capture_{timestamp}.pdf"))
pdf = FPDF()

for img_file in captured_files:
    img = Image.open(img_file)
    pdf_w, pdf_h = 210, 297
    img_w, img_h = img.size
    ratio = min(pdf_w / img_w, pdf_h / img_h)
    pdf_w_scaled, pdf_h_scaled = img_w * ratio, img_h * ratio

    pdf.add_page()
    pdf.image(img_file, x=0, y=0, w=pdf_w_scaled, h=pdf_h_scaled)

pdf.output(pdf_path)
print(f"✅ PDF saved → {pdf_path}")

# PNG 삭제
for f in captured_files:
    os.remove(f)
