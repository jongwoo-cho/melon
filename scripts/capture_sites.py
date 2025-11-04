# scripts/capture_sites.py
import os
import time
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import JavascriptException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image

# ---------- 설정 ----------
KST = timezone(timedelta(hours=9))
timestamp = datetime.now(KST).strftime("%y%m%d_%H%M")
save_dir = "screenshots"
os.makedirs(save_dir, exist_ok=True)

sites = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
}

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1200")
options.add_argument("--lang=ko-KR")
options.add_argument("--disable-notifications")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ---------- 유틸 함수들 ----------
def try_js(js):
    try:
        return driver.execute_script(js)
    except JavascriptException:
        return None

def remove_elements_by_selectors(selectors):
    for sel in selectors:
        try_js(f"document.querySelectorAll('{sel}').forEach(e=>e.remove());")
        time.sleep(0.1)

def hide_high_zindex_overlays():
    js = """
    (function(){
      const els = Array.from(document.querySelectorAll('*'));
      els.forEach(e=>{
        try{
          const s = window.getComputedStyle(e);
          if(!s) return;
          const z = parseInt(s.zIndex)||0;
          if((s.position==='fixed' || s.position==='absolute') && z>1000){
            e.style.display='none';
          }
          // elements covering viewport
          const rect = e.getBoundingClientRect();
          if(rect.width>=window.innerWidth*0.8 && rect.height>=window.innerHeight*0.6 && z>500){
            e.style.display='none';
          }
        }catch(err){}
      });
    })();
    """
    try_js(js)

def remove_iframes_and_try_close():
    # remove iframes whose src contains known ad/pop keywords, and attempt to click close inside iframes
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for f in frames:
        try:
            src = f.get_attribute("src") or ""
            # if iframe src empty or contains 'ads','popup','layer','pop'
            if any(k in src.lower() for k in ["ad", "ads", "popup", "layer", "pop", "consent"]):
                try_js("arguments[0].remove();",)  # fallback; we will remove via JS below
        except Exception:
            pass
    # also remove all iframes (aggressive) that seem likely to be overlays (use cautiously)
    try_js("document.querySelectorAll('iframe').forEach(e=>{ if(!e.id||e.id.toLowerCase().includes('pop')||e.src.includes('popup')) e.remove(); });")

def send_escape_multiple(times=3, sleep_between=0.5):
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        for _ in range(times):
            try:
                body.send_keys(Keys.ESCAPE)
            except:
                pass
            time.sleep(sleep_between)
    except:
        pass

def mutation_cleanup(duration=6.0, interval=0.6):
    """
    Repeatedly run a set of cleaning actions for 'duration' seconds,
    to catch dynamically re-inserted popups.
    """
    t0 = time.time()
    while time.time() - t0 < duration:
        # generic removals
        remove_elements_by_selectors([
            ".popup", ".pop_layer", ".layer_popup", ".layer_pop", ".lyrLayerPop", ".dimmed",
            ".modal", ".modal-backdrop", ".modal-backdrop.fade", ".overlay", ".overlay--dark",
            "#popup", "#popLayer", "#pop", "#cmonLayerPopup"
        ])
        # try to click common close buttons
        for sel in ["button.close", "button.btn_close", ".btn-close", ".close", ".btn_layer_close", ".pop-close", "button[aria-label*='닫기']"]:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    try:
                        e.click()
                    except:
                        pass
        # hide big overlays
        hide_high_zindex_overlays()
        # remove iframes that look like popups
        remove_iframes_and_try_close()
        # send ESC key (some modals close on ESC)
        send_escape_multiple(1, 0.1)
        time.sleep(interval)

# ---------- 사이트별 강력 팝업 핸들러 ----------
def handle_melon():
    # Melon: 광고/이벤트 레이어, 로그인 layer 등. 반복적으로 제거
    try_js("document.querySelectorAll('div[class*=layer], div[class*=popup], iframe').forEach(e=>e.remove());")
    # Try clicking common melon-specific close (best-effort)
    remove_elements_by_selectors(["#wrapPopup", ".lyr_layer", ".pop_close", ".pop-layer", ".pop"])
    mutation_cleanup()

def handle_genie():
    # Genie often has login/modal overlays, try multiple approaches
    try_js("document.querySelectorAll('.popdim, .poplayer, #pop, .ly_wrap, iframe').forEach(e=>e.remove());")
    # force set body overflow
    try_js("document.body.style.overflow='auto';")
    # force add UTF-8 meta and force Nanum font
    try_js("""
      try{
        var m=document.createElement('meta'); m.setAttribute('charset','UTF-8'); document.head.appendChild(m);
      }catch(e){}
      document.querySelectorAll('*').forEach(e=>{ try{ e.style.fontFamily='NanumGothic, Arial, sans-serif'; }catch(e){} });
    """)
    # try clicking several close selectors
    mutation_cleanup()

def handle_bugs():
    # Bugs popups sometimes in iframe; attempt to remove iframe and close
    try_js("document.querySelectorAll('.popup, iframe, .layer, .modal').forEach(e=>e.remove());")
    mutation_cleanup()

def handle_flo():
    # Flo may use shadow DOM or custom components. Remove modal-like tags and overlays.
    try_js("document.querySelectorAll('flo-popup, flo-layer, .modal, .popup, iframe').forEach(e=>e.remove());")
    mutation_cleanup()

# ---------- 캡처 루프 ----------
temp_images = []
for name, url in sites.items():
    print(f"[INFO] Visiting {name}: {url}")
    driver.get(url)
    time.sleep(4)  # initial load

    # site-specific aggressive cleanup
    try:
        if name == "melon":
            handle_melon()
        elif name == "genie":
            handle_genie()
        elif name == "bugs":
            handle_bugs()
        elif name == "flo":
            handle_flo()
    except Exception as e:
        print(f"[WARN] popup handler error for {name}: {e}")

    # final pass: generic
    mutation_cleanup(duration=3, interval=0.5)

    # attempt to scroll to load lazy content
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
    except:
        pass

    # save temporary PNG (will be embedded in PDF then optionally removed)
    img_path = os.path.join(save_dir, f"{name}_{timestamp}.png")
    try:
        driver.save_screenshot(img_path)
        temp_images.append(img_path)
        print(f"[OK] screenshot saved: {img_path}")
    except Exception as e:
        print(f"[ERROR] could not save screenshot for {name}: {e}")

# ---------- PDF 만들기 ----------
pdf_path = os.path.join(save_dir, f"music_sites_{timestamp}.pdf")
try:
    pdf = FPDF()
    # try load Nanum font (GitHub Actions installs fonts-nanum to this path)
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font("NanumGothic", "", font_path, uni=True)
        pdf.set_font("NanumGothic", size=12)
    else:
        pdf.set_font("Arial", size=12)

    for img in temp_images:
        pdf.add_page()
        pdf.cell(0, 8, os.path.basename(img), ln=True, align='C')
        pdf.image(img, x=10, y=20, w=190)  # scale to width
    pdf.output(pdf_path)
    print(f"[OK] PDF created: {pdf_path}")
except Exception as e:
    print(f"[ERROR] PDF creation failed: {e}")

# ---------- 임시 PNG 삭제 ----------
for f in temp_images:
    try:
        os.remove(f)
    except:
        pass

driver.quit()
print("[DONE] Capture finished.")
