import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fpdf import FPDF
from PIL import Image

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

captured_files = []

# -----------------------------------------------------------
# 🔥 벅스 메인페이지 최신음악만 팝업 없이 보이도록 최적화된 전용 제거 함수
# -----------------------------------------------------------
def remove_bugs_main_popups(driver):
    try:
        # 1) 벅스 메인에서 사용하는 모든 팝업 요소 제거
        driver.execute_script("""
            const selectors = [
                '#layPop',
                '.layer-popup',
                '.event_layer',
                '.popup',
                '.modal',
                '.modal-bg',
                '.modal-backdrop',
                '.ad', 
                '#eventLayer'
            ];
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        """)

        # 2) body 스크롤 막힘 해제
        driver.execute_script("""
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
            document.body.classList.remove('no-scroll');
        """)

        # 3) 팝업 재생성 차단
        driver.execute_script("""
            window.open = () => null;

            const blockList = ['layPop', 'eventLayer', 'layer-popup'];
            const observer = new MutationObserver(mutations => {
                mutations.forEach(m => {
                    m.addedNodes.forEach(node => {
                        if (node.id && blockList.includes(node.id)) {
                            node.remove();
                        }
                        if (node.classList) {
                            if ([...node.classList].some(c => c.includes('popup') || c.includes('layer'))) {
                                node.remove();
                            }
                        }
                    });
                });
            });
            observer.observe(document.body, { childList: true, subtree: true });
        """)

    except Exception as e:
        print("[!] Bugs popup removal failed:", e)

# -----------------------------------------------------------
# 사이트별 캡처
# -----------------------------------------------------------
def capture_site(name, url):
    driver.get(url)
    time.sleep(5)

    # FLO 스크롤
    if name == "flo":
        driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(1)

    # 벅스 전용 로직
    if name == "bugs":
        remove_bugs_main_popups(driver)
        time.sleep(1)

    # 일반 사이트 팝업 제거
    else:
        try:
            driver.execute_script("""
                let elems = document.querySelectorAll('[class*="popup"], [id*="popup"], .dimmed, .overlay, .modal');
                elems.forEach(e => e.remove());
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
