import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

OUT_DIR = "screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

def capture():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get("https://www.melon.com/")
        time.sleep(3)

        # 팝업 닫기 시도
        close_selectors = [
            "button[class*=close]",
            "button[aria-label*=닫기]",
            "div[class*=popup] button",
        ]
        for sel in close_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, sel)
                for e in elems:
                    try:
                        e.click()
                        time.sleep(0.5)
                    except:
                        driver.execute_script("arguments[0].remove();", e)
            except:
                pass

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = os.path.join(OUT_DIR, f"melon_{ts}.png")
        driver.save_screenshot(fname)
        print("Saved:", fname)
    finally:
        driver.quit()

if __name__ == "__main__":
    capture()
