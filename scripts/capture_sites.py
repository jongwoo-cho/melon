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

# 한국 표준시 (KST)
KST = timezone(timedelta(hours=9))
now = datetime.now(KST)
timestamp = now.strftime("%y%m%d_%H%M")

# Chrome 옵션
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,3000")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def safe_click(selector):
    try:
        btns = driver.find_elements(By.CSS_SELECTOR, selector)
        for b in btns:
            try:
                b.click()
            except:
                pass
    except:
        pass

def remove_popups():
    driver.execute_script("""
        document.querySelectorAll(
            'iframe, .popup, .layer, #popup, #popLayer, .layer_popup, #modal-root, .dimmed'
        ).forEach(e => e.remove());
        document.body.style.overflow = 'auto';
    """)

def capture_latest_section(name, url, section_selector):
    print(f"🔹 {name} 접속 중...")
    driver.get(url)
    time.sleep(5)

    # 팝업 제거
    remove_popups()
    safe_click("button[aria-label='닫기'], .close, .btn-close, .layer_close")

    time.sleep(2)

    # 캡처
    try:
        section = driver.find_element(By.CSS_SELECTOR, section_selector)
        filename = f"screenshots/{name}_temp.png"
        section.screenshot(filename)
        print(f"✅ {name} 최신음악 영역 캡처 완료")
        return filename
    except Exception as e:
        print(f"⚠️ {name} 영역 캡처 실패 ({e}) — 전체 페이지로 대체 저장")
        filename = f"screenshots/{name}_temp.png"
        driver.save_screenshot(filename)
        return filename

# 🎵 사이트별 최신 음악 섹션
sites = {
    "melon": {
        "url": "https://www.melon.com/",
        "selector": "#conts_section div.new_song_wrap"
    },
    "genie": {
        "url": "https://www.genie.co.kr/",
        "selector": "#new-album, .newest"
    },
    "bugs": {
        "url": "https://music.bugs.co.kr/",
        "selector": "section#newAlbum, .newAlbumSection"
    },
    "flo": {
        "url": "https://www.music-flo.com/",
        "selector": "section[class*='NewMusic'], section[class*='latest'], div[class*='new-song']"
    }
}

captured_files = []

for name, info in sites.items():
    img_path = capture_latest_section(name, info["url"], info["selector"])
    if os.path.exists(img_path):
        captured_files.append(img_path)

driver.quit()

# ----- PDF로 병합 -----
if captured_files:
    pdf_path = f"screenshots/music_latest_{timestamp}.pdf"
    images = [Image.open(p).convert("RGB") for p in captured_files if os.path.exists(p)]
    if images:
        first, rest = images[0], images[1:]
        first.save(pdf_path, save_all=True, append_images=rest)
        print(f"📄 PDF 생성 완료: {pdf_path}")
    else:
        print("⚠️ PDF로 병합할 이미지가 없습니다.")
else:
    print("⚠️ 캡처된 이미지가 없습니다.")

# ----- PNG 임시 파일 삭제 -----
for f in captured_files:
    try:
        os.remove(f)
    except:
        pass

print("🎉 모든 사이트 캡처 및 PDF 병합 완료 (PNG 삭제됨).")
