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
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=ko-KR")  # 지니 한글 깨짐 방지

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 10)

captured_files = []

# -----------------------------------------------------------
# 🔥 벅스 전용 강력 팝업 제거
# -----------------------------------------------------------
def remove_bugs_popups(driver, timeout=6.0):
    try:
        try:
            close_btn_selectors = [
                ".pop_close", ".btn_close", ".btn-close", ".close", ".layerClose",
                ".btnClose", ".lay-close", ".btnClosePop", ".pop_btn_close"
            ]
            for sel in close_btn_selectors:
                try:
                    els = driver.find_elements(By.CSS_SELECTOR, sel)
                    for e in els:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", e)
                            e.click()
                        except:
                            pass
                except:
                    pass

            texts = ["닫기", "닫기닫기", "팝업닫기", "닫", "Close", "close", "×", "✕"]
            for t in texts:
                try:
                    matches = driver.find_elements(By.XPATH, f"//*[text()[normalize-space()='{t}']]")
                    for m in matches:
                        try:
                            m.click()
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", m)
                            except:
                                pass
                except:
                    pass
        except:
            pass

        # ESC 키 여러 번 전송
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            for _ in range(3):
                try:
                    body.send_keys(Keys.ESCAPE)
                    time.sleep(0.3)
                except:
                    pass
        except:
            pass

        # 강력한 DOM 삭제 + MutationObserver 반복 제거
        js = r"""
        (function(timeout_ms){
            function removeNode(n){
                try{
                    if(n && n.parentNode){
                        n.parentNode.removeChild(n);
                    }
                }catch(e){}
            }
            function tryClick(el){
                try{ el.click(); }catch(e){
                    try{ el.dispatchEvent(new Event('click')); }catch(e){}
                }
            }
            const selectors = [
                '#layPop', '#layer_pop', '#popup', '#popupLayer', '.layer-popup',
                '.pop_layer', '.popup', '.modal', '.modal-bg', '.modal-backdrop',
                '.dimmed', '.dimmedLayer', '.popdim', '.ly_wrap', '.ly_pop',
                '.pop_wrap', '.eventLayer', '.evt_layer'
            ];
            const textButtons = ['닫기','닫','팝업닫기','Close','close','×','✕'];

            function strongRemove(){
                selectors.forEach(sel=>{
                    document.querySelectorAll(sel).forEach(el=> removeNode(el));
                });

                document.querySelectorAll('[role="dialog"], [aria-modal="true"]').forEach(el=> removeNode(el));

                Array.from(document.querySelectorAll('div,section')).forEach(el=>{
                    try{
                        const s = (el.className||"") + " " + (el.id||"") + " " + (el.getAttribute('data-role')||"");
                        if(/popup|pop|layer|modal|dimmed|overlay|event/i.test(s)){
                            removeNode(el);
                        }
                    }catch(e){}
                });

                textButtons.forEach(txt=>{
                    Array.from(document.evaluate("//*[text()[normalize-space()='"+txt+"']]", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null))
                        .forEach(el=> tryClick(el));
                });

                Array.from(document.querySelectorAll('body > *')).forEach(el=>{
                    try{
                        const cs = window.getComputedStyle(el);
                        if(cs && (cs.position === 'fixed' || cs.zIndex > 1000)){
                            el.style.display = 'none !important';
                            el.style.visibility = 'hidden !important';
                            el.style.pointerEvents = 'none !important';
                            removeNode(el);
                        }
                    }catch(e){}
                });

                document.querySelectorAll('iframe').forEach(iframe=>{
                    try{
                        const src = (iframe.src||"") + (iframe.getAttribute('data-src')||"");
                        if(/popup|event|layer|ads|banner/i.test(src) || iframe.style.zIndex*1 > 1000){
                            removeNode(iframe);
                        } else {
                            const r = iframe.getBoundingClientRect();
                            if(r.width > window.innerWidth*0.6 && r.height > window.innerHeight*0.6){
                                removeNode(iframe);
                            }
                        }
                    }catch(e){}
                });

                try{
                    document.documentElement.style.overflow = 'auto';
                    document.body.style.overflow = 'auto';
                }catch(e){}
            }

            for(let i=0;i<6;i++){ strongRemove(); }

            const interval = setInterval(strongRemove, 300);

            const observer = new MutationObserver(()=> strongRemove());
            observer.observe(document.documentElement, {childList:true, subtree:true});

            setTimeout(()=>{
                clearInterval(interval);
                observer.disconnect();
            }, timeout_ms);
        })(%d);
        """ % int(timeout * 1000)

        driver.execute_script(js)
        time.sleep(1)

        return True
    except Exception as e:
        print("[!] remove_bugs_popups error:", e)
        return False


# -----------------------------------------------------------
# 🔵 FLO — 오늘 발매 10곡 전체 보이도록 스크롤 조정
# -----------------------------------------------------------
def scroll_flo(driver):
    try:
        # "오늘 발매" 섹션 제목 찾기
        target = driver.find_element(By.XPATH, "//*[contains(text(), '오늘 발매')]")

        # 해당 위치로 스크롤
        driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", target)
        time.sleep(1)

        # 리스트 전체가 보이도록 약간 추가 스크롤
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(1)

    except Exception:
        # fallback — 레이아웃 변경 대비
        driver.execute_script("window.scrollTo(0, 900)")
        time.sleep(1)


# -----------------------------------------------------------
# 사이트별 캡처
# -----------------------------------------------------------
def capture_site(name, url):
    driver.get(url)
    time.sleep(5)

    # FLO 스크롤 강화 버전
    if name == "flo":
        scroll_flo(driver)

    # 벅스 팝업 제거
    elif name == "bugs":
        for _ in range(3):
            remove_bugs_popups(driver, timeout=3.0)
            time.sleep(0.6)

    # 기타 사이트 팝업 제거
    else:
        try:
            driver.execute_script("""
                let elems = document.querySelectorAll('[class*="popup"], [id*="popup"], .dimmed, .overlay, .modal');
                elems.forEach(e => e.remove());
                document.body.style.overflow='auto';
                document.documentElement.style.overflow='auto';
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
