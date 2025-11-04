# scripts/capture_sites.py
import os
import time
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import JavascriptException
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

# ---------- 유틸 ----------
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
    try:
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for f in frames:
            src = f.get_attribute("src") or ""
            if any(k in src.lower() for k in ["ad", "ads", "popup", "layer", "pop", "consent"]):
                try_js("arguments[0].remove();")
        try_js("document.querySelectorAll('iframe').forEach(e=>{ if(!e.id||e.id.toLowerCase().includes('pop')||e.src.includes('popup')) e.remove(); });")
    except Exception:
        pass

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
    t0 = time.time()
    while time.time() - t0 < duration:
        remove_elements_by_selectors([
            ".popup", ".pop_layer", ".layer_popup", ".layer_pop", ".lyrLayerPop", ".dimmed",
            ".modal", ".modal-backdrop", ".overlay", ".overlay--dark",
            "#popup", "#popLayer", "#pop", "#cmonLayerPopup"
        ])
        for sel in ["button.close", "button.btn_close", ".btn-close", ".close", ".btn_layer_close", ".pop-close", "button[aria-label*='닫기']"]:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    e.click()
            except:
                pass
        hide_high_zindex_overlays()
        remove_iframes_and_try_close()
        send_escape_multiple(1, 0.1)
        time.sleep(interval)

# ---------- 사이트별 ----------
def handle_melon():
    try_js("document.querySelectorAll('div[class*=layer], div[class*=popup], iframe').forEach(e=>e.remove());")
    remove_elements_by_selectors(["#wrapPopup", ".lyr_layer", ".pop_close", ".pop-layer", ".pop"])
    mutation_cleanup()

def handle_genie():
    try_js("document.querySelectorAll('.popdim, .poplayer, #pop, .ly_wrap, iframe').forEach(e=>e.remove());")
    try_js("document.body.style.overflow='auto';")
    try_js("""
      try{
        var m=document.createElement('meta'); m.setAttribute('charset','UTF-8'); document.head.appendChild(m);
      }catch(e){}
      document.querySelectorAll('*').forEach(e=>{ try{ e.style.fontFamily='NanumGothic, Arial, sans-serif'; }catch(e){} });
    """)
    mutation_cleanup()

def handle_bugs():
    try_js("document.querySelectorAll('.popup, iframe, .layer, .modal').forEach(e=>e.remove());")
    mutation_cleanup()

def handle_flo():
    try_js("document.querySelectorAll('flo-popup, flo-layer, .modal, .popup, iframe').forEach(e=>e.remove());")
    mutation_cleanup()

# ---------- 캡처 ----------
temp_images = []
for name, url in sites.items():
    print(f"[INFO] Visiting {name}: {url}")
    driver.get(url)
    time.sleep(4)

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

    mutation_cleanup(duration=3, interval=0.5)

    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
    except:
        pass

    img_path = os.path.join(save_dir, f"{name}_{timestamp}.png")
    try:
        driver.save_screenshot(img_path)
        temp_images.append(img_path)
        print(f"[OK] screenshot saved: {img_path}")
    except Exception as e:
        print(f"[ERROR] could not save screenshot for {name}: {e}")

# ---------- PDF ----------
pdf_path = os.path.join(save_dir, f"music_sites_{timestamp}.pdf")
try:
    pdf = FPDF()
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    if os.path.exists(font_path):
        pdf.add_font("NanumGothic", "", font_path, uni=True)
        pdf.set_font("NanumGothic", size=12)
    else:
        pdf.set_font("Arial", size=12)

    for img in temp_images:
        pdf.add_page()
        pdf.cell(0, 8, os.path.basename(img), ln=True, align='C')
        pdf.image(img, x=10, y=20, w=190)
    pdf.output(pdf_path)
    print(f"[OK] PDF created: {pdf_path}")
except Exception as e:
    print(f"[ERROR] PDF creation failed: {e}")

# ---------- PNG 삭제 ----------
for f in temp_images:
    try:
        os.remove(f)
    except:
        pass

driver.quit()
print("[DONE] Capture finished.")
