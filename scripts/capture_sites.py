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

service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 10)

captured_files = []


# -----------------------------------------------------------
# 🔥 벅스 전용 강력 팝업 제거
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

        texts = ["닫기", "닫기닫기", "팝업닫기", "닫", "Close", "close", "×", "✕"]
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
                time.sleep(0.25)
        except:
            pass

        js = r"""
        (function(timeout_ms){
            function removeNode(n){try{if(n&&n.parentNode){n.parentNode.removeChild(n);}}catch(e){}}
            function tryClick(el){try{el.click();}catch(e){try{el.dispatchEvent(new Event('click'));}catch(e){}}}
            const selectors = [
                '#layPop','#layer_pop','#popup','#popupLayer','.layer-popup','.pop_layer','.popup',
                '.modal','.modal-bg','.modal-backdrop','.dimmed','.dimmedLayer','.popdim',
                '.ly_wrap','.ly_pop','.pop_wrap','.eventLayer','.evt_layer'
            ];
            const textButtons = ['닫기','닫','팝업닫기','Close','close','×','✕'];
            function strongRemove(){
                selectors.forEach(sel=>{Array.from(document.querySelectorAll(sel)).forEach(el=>removeNode(el));});
                Array.from(document.querySelectorAll('[role="dialog"],[aria-modal="true"]')).forEach(el=>removeNode(el));
                Array.from(document.querySelectorAll('div,section')).forEach(el=>{
                    try{const s=(el.className||"")+" "+(el.id||"")+" "+(el.getAttribute('data-role')||"");if(/popup|pop|layer|modal|dimmed|overlay|event/i.test(s)){removeNode(el);}}catch(e){}
                });
                textButtons.forEach(txt=>{
                    try{
                        let xp=document.evaluate("//*[text()[normalize-space()='"+txt+"']]",document,null,XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,null);
                        for(let i=0;i<xp.snapshotLength;i++){tryClick(xp.snapshotItem(i));}
                    }catch(e){}
                });
                Array.from(document.querySelectorAll('body>*')).forEach(el=>{
                    try{const cs=window.getComputedStyle(el);if(cs&&(cs.position==='fixed'||cs.position==='sticky'||(parseInt(cs.zIndex)||0)>1000)){removeNode(el);}}catch(e){}
                });
                Array.from(document.querySelectorAll('iframe')).forEach(iframe=>{
                    try{
                        const src=(iframe.src||"")+(iframe.getAttribute('data-src')||"");
                        if(/popup|event|layer|ads|adservice|banner/i.test(src)||(parseInt(iframe.style.zIndex)||0)>1000){removeNode(iframe);}
                        else{const r=iframe.getBoundingClientRect();if(r.width>window.innerWidth*0.6 && r.height>window.innerHeight*0.6){removeNode(iframe);}}
                    }catch(e){}
                });
                try{document.documentElement.style.overflow='auto';document.body.style.overflow='auto';}catch(e){}
            }
            for(let i=0;i<6;i++){try{strongRemove();}catch(e){}}
            const interval=setInterval(function(){try{strongRemove();}catch(e){}},300);
            const observer=new MutationObserver(function(){try{strongRemove();}catch(e){}});
            try{observer.observe(document.documentElement||document.body,{childList:true,subtree:true});}catch(e){}
            setTimeout(function(){try{clearInterval(interval);observer.disconnect();}catch(e){}},timeout_ms);
            try{document.documentElement.style.overflow='auto';document.body.style.overflow='auto';}catch(e){}
        })(%d);
        """ % int(timeout * 1000)
        driver.execute_script(js)
        time.sleep(min(1.0, timeout / 3.0))
        return True
    except Exception as e:
        print("[!] remove_bugs_popups error:", e)
        return False


# -----------------------------------------------------------
# 🔵 FLO 처리 — 팝업 제거 + 캡처 영역 더 내려서 표시
# -----------------------------------------------------------
def handle_flo(driver):
    try:
        driver.execute_script("""
            let selectors=['.popup','.pop','.modal','.layer','.event-popup','[class*="Popup"]','[id*="popup"]','.cookie','.cookie-popup'];
            selectors.forEach(sel=>{document.querySelectorAll(sel).forEach(e=>e.remove());});
            document.body.style.overflow='auto';
            document.documentElement.style.overflow='auto';
        """)
    except:
        pass
    time.sleep(0.5)

    try:
        el = driver.find_element(By.XPATH, "//h2[contains(text(),'오늘 발매')]")
        driver.execute_script("arguments[0].scrollIntoView(true);", el)
        time.sleep(0.5)
        driver.execute_script("window.scrollBy(0,120);")  # 캡처 영역 더 아래로 스크롤
        time.sleep(0.5)
    except:
        driver.execute_script("window.scrollTo(0,600)")
        time.sleep(0.5)


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
                let elems=document.querySelectorAll('[class*="popup"],[id*="popup"],.dimmed,.overlay,.modal');
                elems.forEach(e=>e.remove());
                document.body.style.overflow='auto';
                document.documentElement.style.overflow='auto';
            """)
        except:
            pass

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
