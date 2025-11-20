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

# Chrome 옵션 (headless)
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
# 벅스 강력 팝업 제거 (기존 로직 유지)
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

        # JS 로 반복 제거
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
                Array.from(document.querySelectorAll('div, section')).forEach(el => {
                    try {
                        const s = (el.className||"") + " " + (el.id||"") + " " + (el.getAttribute('data-role')||"");
                        if(/popup|layer|modal|dimmed|overlay|event/i.test(s)){
                            removeNode(el);
                        }
                    } catch(e) {}
                });
                texts.forEach(txt => {
                    let xp = document.evaluate(
                        "//*[text()[normalize-space()='"+txt+"']]",
                        document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null
                    );
                    for (let i = 0; i < xp.snapshotLength; i++){
                        tryClick(xp.snapshotItem(i));
                    }
                });
                Array.from(document.querySelectorAll('body > *')).forEach(el => {
                    try {
                        const cs = window.getComputedStyle(el);
                        if (cs && (cs.position === 'fixed' || cs.zIndex > 1000)){
                            removeNode(el);
                        }
                    } catch(e){}
                });
                document.querySelectorAll('iframe').forEach(ifr => {
                    try {
                        const src = (ifr.src||"") + (ifr.getAttribute('data-src')||"");
                        if (/popup|event|layer|ads|banner/i.test(src) || (parseInt(ifr.style.zIndex)||0) > 1000) {
                            removeNode(ifr);
                        } else {
                            const r = ifr.getBoundingClientRect();
                            if (r.width > window.innerWidth * 0.6 && r.height > window.innerHeight * 0.6) {
                                removeNode(ifr);
                            }
                        }
                    } catch(e){}
                });
                document.documentElement.style.overflow = 'auto';
                document.body.style.overflow = 'auto';
            }
            for (let i = 0; i < 6; i++) { try { strongRemove(); } catch(e) {} }
            const interval = setInterval(strongRemove, 300);
            const observer = new MutationObserver(strongRemove);
            try { observer.observe(document.documentElement || document.body, { childList: true, subtree: true }); } catch(e){}
            setTimeout(function(){
                clearInterval(interval);
                observer.disconnect();
            }, timeout_ms);
        })(%d);
        """ % int(timeout * 1000)
        driver.execute_script(js)
        time.sleep(min(1.0, timeout / 3.0))
        return True
    except Exception as e:
        print("[!] remove_bugs_popups error:", e)
        return False


# -----------------------------------------------------------
# 🔵 FLO 처리 전략 — 팝업 제거 + 확실한 아래 스크롤
# -----------------------------------------------------------
def handle_flo(driver):
    # 팝업 제거
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
    time.sleep(0.7)

    # 전략 조합: 여러 방식으로 스크롤을 시도
    # 1) 제목 요소 + 컨테이너 기반 스크롤
    try:
        header = driver.find_element(By.XPATH, "//h2[contains(text(),'오늘 발매')]")
        # scroll header into view
        driver.execute_script("arguments[0].scrollIntoView({block:'start'});", header)
        time.sleep(0.5)

        # 2) 바로 아래 리스트 컨테이너의 높이를 구해서 동적으로 스크롤
        list_container_h = driver.execute_script("""
            let header = arguments[0];
            // 부모 또는 옆의 리스트 컨테이너 찾기 (예: ul, div)
            let cont = header.nextElementSibling;
            if (!cont) cont = header.parentElement;
            if (!cont) return 0;
            return cont.getBoundingClientRect().height;
        """, header)

        if list_container_h and list_container_h > 0:
            # 화면 높이 계산 + 컨테이너 절반 정도 아래로 스크롤
            driver.execute_script(f"window.scrollBy(0, {list_container_h * 0.5});")
        else:
            # fallback: 절대값 스크롤
            driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(0.5)

        # 3) 마지막 카드 요소(10번째 곡)까지 스크롤, 그 후 위로 보정
        try:
            # 예: 리스트 카드들이 <li> 또는 div.card 형태라 가정
            cards = driver.find_elements(By.CSS_SELECTOR, "div.trackListItem, li.track-list__item, div.card, li.card")
            if len(cards) >= 10:
                last = cards[9]  # 10번째 요소 (0-indexed)
            else:
                last = cards[-1]
            driver.execute_script("arguments[0].scrollIntoView(true);", last)
            time.sleep(0.5)
            # 마지막까지 가고 나서 조금 위로 당겨서 전체 리스트 보이게
            driver.execute_script("window.scrollBy(0, -100);")
            time.sleep(0.5)
        except Exception:
            pass

    except Exception as e:
        # 안전 장치 fallback
        print("[!] FLO scroll 전략 1 실패:", e)
        driver.execute_script("window.scrollTo(0, 900)")
        time.sleep(0.5)

    # 4) 반복 시도: 동적 로딩이 있을 경우
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(0.4)


# -----------------------------------------------------------
# 사이트별 캡처
# -----------------------------------------------------------
def capture_site(name, url):
    driver.get(url)
    time.sleep(5)

    if name == "flo":
        handle_flo(driver)
    elif name == "bugs":
        for _ in range(3):
            remove_bugs_popups(driver, timeout=3.0)
            time.sleep(0.6)
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
