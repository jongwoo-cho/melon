import os
import time
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

# 저장 폴더
os.makedirs("screenshots", exist_ok=True)

# 한국 표준시 기준 시간
KST = timezone(timedelta(hours=9))
timestamp = datetime.now(KST).strftime("%y%m%d_%H%M")

# Chrome 옵션
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,3000")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# ---------------------------
# 공통 유틸
# ---------------------------
def hard_popup_clean():
    """공통 팝업 제거"""
    driver.execute_script("""
        document.querySelectorAll(
            'iframe, .popup, .layer_popup, .dimmed, #popLayer, #modal-root, .modal, .overlay'
        ).forEach(e => e.remove());
        document.body.style.overflow = 'auto';
    """)

def close_popup_buttons(selectors):
    """닫기 버튼을 여러 방식으로 클릭 시도"""
    for sel in selectors:
        for el in driver.find_elements(By.CSS_SELECTOR, sel):
            try:
                el.click()
                time.sleep(0.3)
            except:
                pass

def capture_section(name, url, selector, popup_handler=None):
    print(f"🔹 {name} 접속 중...")
    driver.get(url)
    time.sleep(5)

    if popup_handler:
        popup_handler()
    else:
        hard_popup_clean()

    time.sleep(2)

    try:
        section = driver.find_element(By.CSS_SELECTOR, selector)
        filename = f"screenshots/{name}_temp.png"
        section.screenshot(filename)
        print(f"✅ {name} 최신 음악 영역 캡처 완료")
        return filename
    except Exception as e:
        print(f"⚠️ {name} 영역 캡처 실패 ({e}) → 전체 페이지 저장")
        fallback = f"screenshots/{name}_temp.png"
        driver.save_screenshot(fallback)
        return fallback

# ---------------------------
# 사이트별 팝업 핸들러
# ---------------------------
def melon_popups():
    close_popup_buttons(["#layer_popup_close", ".btn_close", ".wrap_popup button", "button[aria-label='닫기']"])
    hard_popup_clean()

def genie_popups():
    close_popup_buttons([".popup-close", ".close", "button[aria-label='닫기']", ".btn-close"])
    # EUC-KR → UTF-8 메타태그 강제 + 나눔고딕 폰트 적용
    try:
        driver.execute_script("""
            var meta = document.createElement('meta');
            meta.setAttribute('charset', 'UTF-8');
            document.head.appendChild(meta);
            document.querySelectorAll('*').forEach(e => {
                e.style.fontFamily = 'NanumGothic, sans-serif';
            });
        """)
    except:
        pass
    hard_popup_clean()

def bugs_popups():
    close_popup_buttons([".layerClose", ".btnClose", ".popupClose", "button[aria-label='닫기']"])
    hard_popup_clean()

def flo_popups():
    close_popup_buttons([".btn_close", "button[aria-label='닫기']", "button[class*='close']"])
    # shadow DOM 기반 팝업 제거
    driver.execute_script("""
        document.querySelectorAll('flo-popup, flo-layer, [id*="modal"]').forEach(e => e.remove());
    """)
    hard_popup_clean()

# ---------------------------
# 사이트 정의
# ---------------------------
sites = {
    "melon": {
        "url": "https://www.melon.com/",
        "selector": "#conts_section div.new_song_wrap",
        "popup": melon_popups
    },
    "genie": {
        "url": "https://www.genie.co.kr/",
        "selector": "#new-album, .newest, .new-album",
        "popup": genie_popups
    },
    "bugs": {
        "url": "https://music.bugs.co.kr/",
        "selector": "section#newAlbum, .newAlbumSection",
        "popup": bugs_popups
    },
    "flo": {
        "url": "https://www.music-flo.com/",
        "selector": "section[class*='NewMusic'], section[class*='latest'], div[class*='new-song']",
        "popup": flo_popups
    }
}

# ---------------------------
# 실행
# ---------------------------
captured_files = []

for name, info in sites.items():
    path = capture_section(name, info["url"], info["selector"], info["popup"])
    captured_files.append(path)

driver.quit()

# ---------------------------
# PDF 병합
# ---------------------------
if captured_files:
    pdf_path = f"screenshots/music_latest_{timestamp}.pdf"
    images = [Image.open(p).convert("RGB") for p in captured_files if os.path.exists(p)]
    if images:
        first, rest = images[0], images[1:]
        first.save(pdf_path, save_all=True, append_images=rest)
        print(f"📄 PDF 생성 완료: {pdf_path}")

# ---------------------------
# PNG 임시파일 삭제
# ---------------------------
for p in captured_files:
    try:
        os.remove(p)
    except:
        pass

print("🎉 모든 사이트 최신음악 PDF 캡처 완료 (팝업 제거 + 한글 폰트 적용됨)")
