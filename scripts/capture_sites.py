import os
import time
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF  # PDF 변환용

# ---------- 한국 시간 ----------
KST = timezone(timedelta(hours=9))
timestamp = datetime.now(KST).strftime("%y%m%d_%H%M")

# ---------- 저장 폴더 ----------
save_dir = "screenshots"
os.makedirs(save_dir, exist_ok=True)

# ---------- 사이트 목록 ----------
sites = {
    "melon": "https://www.melon.com/",
    "genie": "https://www.genie.co.kr/",
    "bugs": "https://music.bugs.co.kr/",
    "flo": "https://www.music-flo.com/",
}

# ---------- 브라우저 옵션 ----------
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-notifications")
options.add_argument("--lang=ko-KR")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ---------- PDF 생성기 ----------
pdf = FPDF()
pdf.add_font("NanumGothic", "", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", uni=True)

for name, url in sites.items():
    print(f"▶ {name.upper()} 방문 중...")
    driver.get(url)
    time.sleep(5)

    # ---------- 사이트별 팝업 제거 ----------
    if name == "melon":
        # 팝업 iframe / layer 강제 제거
        driver.execute_script("""
            const popups = document.querySelectorAll('div[style*="z-index"], .layer_popup, iframe');
            popups.forEach(p => p.remove());
        """)
        driver.execute_script("document.body.style.overflow='auto';")

    elif name == "genie":
        # 로그인 유도, 광고 팝업, 배경 블러 제거
        driver.execute_script("""
            const blocks = document.querySelectorAll('#popup, .popup, .dimmed, .ly_popup, iframe');
            blocks.forEach(el => el.remove());
            document.body.style.overflow='auto';
        """)

    elif name == "bugs":
        driver.execute_script("""
            const ads = document.querySelectorAll('.popup, iframe, .layer, .modal');
            ads.forEach(e => e.remove());
        """)

    elif name == "flo":
        driver.execute_script("""
            const popups = document.querySelectorAll('.modal, .popup, iframe');
            popups.forEach(p => p.remove());
        """)

    time.sleep(2)

    # ---------- 캡처 ----------
    img_path = os.path.join(save_dir, f"{name}_{timestamp}.png")
    driver.save_screenshot(img_path)
    print(f"📸 {name} 캡처 완료 → {img_path}")

    # ---------- PDF에 삽입 ----------
    pdf.add_page()
    pdf.set_font("NanumGothic", "", 14)
    pdf.cell(0, 10, f"{name.upper()} ({timestamp})", ln=True, align="C")
    pdf.image(img_path, x=10, y=25, w=190)

driver.quit()

# ---------- PDF 저장 ----------
pdf_path = os.path.join(save_dir, f"music_sites_{timestamp}.pdf")
pdf.output(pdf_path)
print(f"✅ PDF 저장 완료 → {pdf_path}")
