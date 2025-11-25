import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from openpyxl import Workbook

URL = "https://music.apple.com/kr/new"

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                            options=options)


def scrape_new_music(driver):
    """새로운 음악(캐러셀) – 화살표 넘기며 전체 수집"""
    results = set()

    try:
        section = driver.find_element(By.XPATH, "//h2[contains(text(), '새로운 음악')]/ancestor::section")
    except:
        return []

    # 캐러셀 내부 첫 컨테이너 찾기
    cards = section.find_elements(By.CSS_SELECTOR, "div.shelf-grid__item")
    results |= extract_album_artist(cards)

    # 화살표 버튼 반복 클릭
    while True:
        try:
            next_button = section.find_element(By.CSS_SELECTOR, "button[aria-label='다음']")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(1.2)

            cards = section.find_elements(By.CSS_SELECTOR, "div.shelf-grid__item")
            results |= extract_album_artist(cards)

        except:
            break

    return list(results)


def extract_album_artist(card_elements):
    """카드 리스트에서 앨범명-아티스트명 추출"""
    results = set()
    for c in card_elements:
        try:
            album = c.find_element(By.CSS_SELECTOR, "div.shelf-grid__title").text.strip()
            artist = c.find_element(By.CSS_SELECTOR, "div.shelf-grid__subtitle").text.strip()
            if album and artist:
                results.add((album, artist))
        except:
            continue
    return results


def scrape_static_section(driver, title):
    """최신곡 / 최신 발매 – 전체 리스트 수집"""
    try:
        section = driver.find_element(By.XPATH, f"//h2[contains(text(), '{title}')]/ancestor::section")
    except:
        return []

    cards = section.find_elements(By.CSS_SELECTOR, "div.shelf-grid__item")
    return list(extract_album_artist(cards))


def save_to_excel(data_new, data_recent, data_release):
    """데이터를 날짜 기반 파일명으로 저장"""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"apple_music_{today}.xlsx"

    wb = Workbook()

    # Sheet 1: 새로운 음악
    ws1 = wb.active
    ws1.title = "새로운 음악"
    ws1.append(["앨범명", "아티스트명"])
    for album, artist in data_new:
        ws1.append([album, artist])

    # Sheet 2: 최신곡
    ws2 = wb.create_sheet("최신곡")
    ws2.append(["앨범명", "아티스트명"])
    for album, artist in data_recent:
        ws2.append([album, artist])

    # Sheet 3: 최신 발매
    ws3 = wb.create_sheet("최신 발매")
    ws3.append(["앨범명", "아티스트명"])
    for album, artist in data_release:
        ws3.append([album, artist])

    wb.save(filename)


def main():
    driver = get_driver()
    driver.get(URL)
    time.sleep(3)

    print("🔍 새로운 음악 수집 중…")
    new_music = scrape_new_music(driver)

    print("🔍 최신곡 수집 중…")
    recent_tracks = scrape_static_section(driver, "최신곡")

    print("🔍 최신 발매 수집 중…")
    new_release = scrape_static_section(driver, "최신 발매")

    print("💾 엑셀 저장 중…")
    save_to_excel(new_music, recent_tracks, new_release)

    driver.quit()
    print("완료!")


if __name__ == "__main__":
    main()
