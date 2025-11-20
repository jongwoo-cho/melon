import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image

# selenium helpers
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
# 🔥 벅스 전용 강력한 팝업 제거 (업데이트된 버전)
# - 클릭으로 닫기 시도
# - 반복 DOM 제거 (setInterval 방식)
# - iframe & shadow DOM 처리
# - CSS 강제 숨김 (z-index, pointer-events)
# - ESC 키 전송
# -----------------------------------------------------------
def remove_bugs_popups(driver, timeout=6.0):
    """
    driver: selenium webdriver
    timeout: how many seconds we aggressively try to remove dynamic popups
    """
    try:
        # 1) Try clicking common close buttons by selector and by innerText
        try:
            # Attempt to click known close buttons quickly
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

            # Click by visible text (Korean/English)
            texts = ["닫기", "닫기닫기", "팝업닫기", "닫", "Close", "close", "×", "✕"]
            for t in texts:
                try:
                    # using XPath to match visible text
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
        except Exception as e:
            print("[!] initial click attempts failed:", e)

        # 2) Send ESC a few times (some overlays close on ESC)
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

        # 3) Inject robust JS that:
        #  - removes matching selectors
        #  - hides overlays with high z-index
        #  - removes iframes that look like popups
        #  - walks shadowRoots and removes nodes inside them
        #  - installs a MutationObserver / interval to keep removing for `timeout` seconds
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
                try{
                    el.click();
                }catch(e){
                    try{ el.dispatchEvent(new Event('click')); }catch(e){}
                }
            }
            // selectors and heuristics
            const selectors = [
                '#layPop', '#layer_pop', '#popup', '#popupLayer', '.layer-popup', '.pop_layer', '.popup',
                '.modal', '.modal-bg', '.modal-backdrop', '.dimmed', '.dimmedLayer', '.popdim',
                '.ly_wrap', '.ly_pop', '.pop_wrap', '.eventLayer', '.evt_layer'
            ];
            const textButtons = ['닫기','닫','팝업닫기','Close','close','×','✕'];

            function strongRemove(){
                // remove by selector
                selectors.forEach(sel=>{
                    document.querySelectorAll(sel).forEach(el=>{
                        removeNode(el);
                    });
                });
                // remove elements with role=dialog or aria-modal
                document.querySelectorAll('[role="dialog"], [aria-modal="true"]').forEach(el=>{
                    removeNode(el);
                });
                // remove by attribute heuristics
                Array.from(document.querySelectorAll('div,section')).forEach(el=>{
                    try{
                        const s = (el.className||"") + " " + (el.id||"") + " " + (el.getAttribute('data-role')||"");
                        if(/popup|pop|layer|modal|dimmed|overlay|event/i.test(s)){
                            removeNode(el);
                        }
                    }catch(e){}
                });
                // try to click close-like elements by innerText
                textButtons.forEach(txt=>{
                    Array.from(document.evaluate("//*[text()[normalize-space()='"+txt+"']]", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null)).forEach(i=>{
                        tryClick(i);
                    });
                });

                // hide overlays by style
                Array.from(document.querySelectorAll('body > *')).forEach(el=>{
                    try{
                        const cs = window.getComputedStyle(el);
                        if(cs && (cs.position === 'fixed' || cs.position === 'sticky' || cs.zIndex > 1000 || cs.pointerEvents === 'none' )){
                            el.style.display = 'none !important';
                            el.style.visibility = 'hidden !important';
                            el.style.pointerEvents = 'none !important';
                            removeNode(el);
                        }
                    }catch(e){}
                });

                // remove iframes that look like popups
                document.querySelectorAll('iframe').forEach(iframe=>{
                    try{
                        const src = (iframe.src||"") + (iframe.getAttribute('data-src')||"");
                        if(/popup|event|layer|ads|adservice|banner/i.test(src) || iframe.style.zIndex*1 > 1000){
                            removeNode(iframe);
                        } else {
                            // try to set display none if iframe covers much of screen
                            const r = iframe.getBoundingClientRect();
                            if(r.width > window.innerWidth*0.6 && r.height > window.innerHeight*0.6){
                                removeNode(iframe);
                            }
                        }
                    }catch(e){}
                });

                // shadow DOM traversal: try to remove nodes inside shadow roots or remove hosts
                function walkAndRemove(node){
                    try{
                        if(node.shadowRoot){
                            node.shadowRoot.querySelectorAll('*').forEach(inner=>{
                                try{ removeNode(inner); }catch(e){}
                            });
                            removeNode(node);
                        }
                        node.querySelectorAll && node.querySelectorAll('*').forEach(child=>{
                            if(child.shadowRoot){
                                child.shadowRoot.querySelectorAll('*').forEach(c=>{
                                    try{ removeNode(c); }catch(e){}
                                });
                                removeNode(child);
                            }
                        });
                    }catch(e){}
                }
                walkAndRemove(document);
            }

            // run immediately a few times
            for(let i=0;i<6;i++){
                try{ strongRemove(); }catch(e){}
            }

            // interval to repeatedly clear dynamic popups
            const interval = setInterval(function(){
                try{ strongRemove(); }catch(e){}
            }, 300);

            // observer to catch newly added nodes fast
            const observer = new MutationObserver(function(mutations){
                try{
                    strongRemove();
                }catch(e){}
            });
            observer.observe(document.documentElement || document.body, {childList:true, subtree:true, attributes:false});

            // stop observer/interval after timeout
            setTimeout(function(){
                try{
                    clearInterval(interval);
                    observer.disconnect();
                }catch(e){}
            }, timeout_ms);

            // final attempt: force-enable scroll and remove overflow hidden
            document.documentElement.style.overflow = 'auto';
            document.body.style.overflow = 'auto';
        })(%d);
        """ % int(timeout * 1000)

        driver.execute_script(js)
        # allow some time for the JS to act
        time.sleep(min(1.0, timeout/3.0))

        # 4) Try clicking close buttons again after JS removal (some close buttons are created after script runs)
        try:
            for _ in range(3):
                try:
                    close_candidates = driver.find_elements(By.XPATH, "//*[contains(@class,'close') or contains(@class,'Close') or contains(@id,'close') or contains(@aria-label,'close')]")
                    for c in close_candidates:
                        try:
                            driver.execute_script("arguments[0].click();", c)
                        except:
                            pass
                except:
                    pass
                time.sleep(0.3)
        except:
            pass

        # 5) Final ESC attempts and small wait to ensure overlays gone
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            for _ in range(2):
                try:
                    body.send_keys(Keys.ESCAPE)
                    time.sleep(0.2)
                except:
                    pass
        except:
            pass

        # 6) Remove any remaining inline overlay styles and set pointer-events back to normal
        try:
            driver.execute_script("""
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
                Array.from(document.querySelectorAll('*')).forEach(el=>{
                    try{
                        el.style.pointerEvents = 'auto';
                        if(el.style && (el.style.display === 'none' || el.style.visibility === 'hidden')){
                            // leave hidden removed nodes alone
                        }
                    }catch(e){}
                });
            """)
        except:
            pass

        return True
    except Exception as e:
        print("[!] remove_bugs_popups error:", e)
        return False

# -----------------------------------------------------------
# 사이트별 캡처 (기존 로직 유지, 벅스만 강화)
# -----------------------------------------------------------
def capture_site(name, url):
    driver.get(url)
    # 기본 로딩 대기
    time.sleep(5)

    # FLO 스크롤 (기존 유지)
    if name == "flo":
        driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(1)

    # 벅스 전용 팝업 제거 (강력 버전)
    if name == "bugs":
        # 시도 횟수 늘려서 여러번 제거 시도
        success = False
        for attempt in range(3):
            remove_bugs_popups(driver, timeout=3.0)
            time.sleep(0.6)  # allow page to settle
            # try to see if any overlay-like elements remain (quick heuristic)
            try:
                overlays = driver.execute_script("""
                    return Array.from(document.querySelectorAll('div,section,dialog'))
                        .filter(e=> {
                            try{
                                const cs = window.getComputedStyle(e);
                                return (cs && (cs.position==='fixed' || cs.zIndex*1>999 || cs.pointerEvents==='none' || cs.visibility==='visible')) && e.offsetWidth>0 && e.offsetHeight>0;
                            }catch(e){ return false; }
                        }).slice(0,5).map(e=>e.outerHTML);
                """)
                if not overlays:
                    success = True
                    break
            except:
                pass
        if not success:
            print("[!] 벅스 팝업 제거를 여러 번 시도했지만 일부 요소가 남아있을 수 있습니다. 스크린샷에서 보정 필요.")
    else:
        # 다른 사이트 팝업 제거 (기존 방식 유지)
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
# PNG → PDF 변환 (기존 로직)
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
