import os
import time
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from fpdf import FPDF
from PIL import Image

# ====== 기본 설정 ======
KST = pytz.timezone("Asia/Seoul")
now = datetime.now(KST)
today = now.strftime("%Y%m%d_%H%M")
base_dir = f"./capture/{today}"
os.makedirs(base_dir, exist_ok=True)

options = webdriver.ChromeOptions()
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# ====== 캡처 함수 ======
def take_screenshot(name):
    screenshot_path = os.path.join(base_dir, f"{name}.png")
    driver.save_screenshot(screenshot_path)
    print(f"{name} 캡처 완료")
    return screenshot_path


# ====== PDF 변환 ======
def images_to_pdf(image_paths, output_path):
    pdf = FPDF(unit="pt", format=[1080, 1920])
    for img in image_paths:
        image = Image.open(img)
        width, height = image.size
        pdf.add_page()
        pdf.image(img, 0, 0, width, height)
    pdf.output(output_path, "F")


# ====== 사이트 정보 ======
sites = [
    {"name": "melon", "url": "https://www.melon.com/new/album/listPaging.htm"},
    {"name": "genie", "url": "https://www.genie.co.kr/newest"},
    {"name": "bugs", "url": "https://music.bugs.co.kr/newest/album"},
    {"name": "flo",   "url": "https://www.music-flo.com/location/home"},
]


# ====== 메인 실행 ======
captured_images = []

for site in sites:
    name = site["name"]
    url = site["url"]

    print(f"\n=== {name.upper()} 시작 ===")

    driver.get(url)
    time.sleep(3)

    # ------------------------------------------
    # ① 사이트별 팝업 제거 로직
    # ------------------------------------------

    if name == "melon":
        try:
            driver.find_element(By.CSS_SELECTOR, ".guide_close").click()
        except:
            pass

    elif name == "genie":
        try:
            driver.execute_script("document.querySelector('.popup-close')?.click()")
        except:
            pass

    elif name == "bugs":
        # 기존 로직 그대로 유지 (여러 실패 대응)
        try:
            # 가장 흔한 팝업 닫기 버튼
            driver.execute_script("""
                document.querySelectorAll('.layerClose, .btnClose, .popupClose').forEach(btn => btn.click());
            """)
            time.sleep(1)
        except:
            pass

        try:
            # 광고 팝업 iframe 제거
            driver.execute_script("""
                document.querySelectorAll("iframe").forEach(f=>{
                    if (f.src.includes("ads") || f.src.includes("ad")) f.remove();
                });
            """)
        except:
            pass

        try:
            # body overflow 복구
            driver.execute_script("document.body.style.overflow='auto'")
        except:
            pass

    elif name == "flo":
        # ------------------------------------------
        # FLO 팝업 제거 강화 (이번 요청)
        # ------------------------------------------
        try:
            # 어떤 팝업이든 닫기 버튼 형태를 강제 클릭
            driver.execute_script("""
                document.querySelectorAll(
                    '.btn-close, .close, .popup-close, .modal-close, [class*="Close"], button[aria-label="close"]'
                ).forEach(btn => btn.click());
            """)
            time.sleep(0.5)
        except:
            pass

        try:
            # FLO 특유 프로모션 팝업 제거
            driver.execute_script("""
                document.querySelectorAll('.promotion, .popup, .modal').forEach(p => p.remove());
            """)
        except:
            pass

        # -------------------------------------------------
        # ② FLO 스크롤 조정 — '오늘 발매 음악' 10곡 전부 보이도록
        # -------------------------------------------------
        time.sleep(1)

        try:
            # "오늘 발매" 텍스트 찾기
            target = driver.find_element(
                By.XPATH, "//*[contains(text(), '오늘 발매')]"
            )

            # 그 위치로 이동
            driver.execute_script("arguments[0].scrollIntoView({block: 'start'});", target)
            time.sleep(1)

            # 10곡 모두 나오도록 살짝 위/아래 조정
            driver.execute_script("window.scrollBy(0, -150)")  # 조금 위로 올림
            driver.execute_script("window.scrollBy(0, 350)")   # 실제 카드 10개 보이게 최종 조정
            time.sleep(1)

        except:
            # fallback 레이아웃 대응
            driver.execute_script("window.scrollTo(0, 950)")
            time.sleep(1)

    # ------------------------------------------
    # ③ 캡처 실행
    # ------------------------------------------
    img = take_screenshot(name)
    captured_images.append(img)


# ====== PDF 변환 ======
output_pdf = os.path.join(base_dir, f"{today}.pdf")
images_to_pdf(captured_images, output_pdf)

print("\n=== 모든 캡처 및 PDF 변환 완료 ===")
print("저장 위치:", output_pdf)
driver.quit()
