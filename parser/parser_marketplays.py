import os
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import sqlite3



# === function to download images ===
def download_image(image_url, title):
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(image_url, headers=headers, stream=True)
        if response.status_code == 200:
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
            filename = f"media/{safe_title}.jpg"
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return filename
        else:
            print(f"error downloading image: {image_url}")
            return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


# === initialization of the browser ===
def init_browser():
    print("🔧 init_browser() called")
    
    # Настройки браузера
    options = webdriver.ChromeOptions()
    print("🔧 Setting up Chrome options...")
    options.add_argument('--headless=new')  # Новый headless режим в Chrome 115+
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')

    print("🔧 Chrome options configured")

    try:
        print("🔧 Connecting to Selenium Hub...")
        # Подключаемся к Selenium Hub
        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=options
        )
        print("🔧 Successfully connected to Selenium Hub")
        
        # Скрываем WebDriver свойства
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("🔧 WebDriver property hidden")
        
        return driver
    except Exception as e:
        print(f"❌ Error initializing browser: {e}")
        import traceback
        traceback.print_exc()
        return None


# === parsing search page ===
def parse_search_page(driver, keyword, max_pages=1):
    all_links = []
    print(f"🔍 Starting search for keyword: '{keyword}' on {max_pages} pages")

    for page in range(1, max_pages + 1):
        url = f"https://www.marktplaats.nl/q/ {keyword.replace(' ', '+')}/p/{page}/"
        print(f"📄 Parsing page {page}: {url}")

        try:
            driver.get(url)
            print(f"✅ Page loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            continue

        # Ждём загрузки товаров
        try:
            print("⏳ Waiting for products to load...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.hz-Listing"))
            )
            print("✅ Products loaded successfully")
        except Exception as e:
            print(f"❌ Products not loaded on page: {e}")
            continue

        # Прокрутка для подгрузки всех элементов
        print("📜 Scrolling to load all elements...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        items = driver.find_elements(By.CSS_SELECTOR, "li.hz-Listing")
        print(f"📦 Found {len(items)} items on page {page}")

        for i, item in enumerate(items, 1):
            try:
                link_tag = item.find_element(By.CSS_SELECTOR, "a.hz-Listing-coverLink")
                actions = ActionChains(driver)
                actions.move_to_element(link_tag).perform()
                time.sleep(0.5)

                href = link_tag.get_attribute("href")
                if href:
                    all_links.append(href)
                    print(f"🔗 Added link {i}: {href}")
                else:
                    print(f"⚠️ Skipped link {i} (None)")
            except Exception as e:
                print(f"❌ Error processing item {i}: {e}")

    print(f"📋 Total links collected: {len(all_links)}")
    return all_links


# === parsing product page ===
def parse_product_page(driver, url, exclude_keywords=None, min_price=None, max_price=None):
    print(f"🔍 Parsing product page: {url}")
    os.makedirs("media", exist_ok=True)
    try:
        driver.get(url)
        print(f"✅ Product page loaded")
        time.sleep(3)  # Wait for JS to execute
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # title
        title_tag = soup.find("h1", {"class": "Listing-title"})
        title = title_tag.text.strip() if title_tag else "product"
        print(f"📝 Title: {title}")

        # full description
        description_div = soup.find("div", {"class": "Description-description"})
        full_description = description_div.get_text(separator="\n", strip=True) if description_div else ""
        print(f"📄 Description length: {len(full_description)} chars")

        # condition
        condition_span = soup.find("span", {"class": "Attributes-value"})
        condition = condition_span.text.strip() if condition_span else ""
        print(f"🏷️ Condition: {condition}")

        # date
        stats = soup.select(".Stats-summary")
        if len(stats) >= 3:
            date_tag = stats[2]
            date = date_tag.get_text(strip=True)
        else:
            date = "Не указана"
        print(f"📅 Date: {date}")

        # price
        price_tag = soup.find('div', {'class': 'Listing-price'})
        price_str = price_tag.text.strip() if price_tag else ''
        print(f"💰 Raw price: {price_str}")

        cleaned_price = re.sub(r'[^\d.,]', '', price_str)

        if ',' in cleaned_price and cleaned_price.count(',') == 1:
            parts = cleaned_price.split(',')
            integer_part = parts[0]
            decimal_part = parts[1][:2]
            formatted_price = f"{integer_part}.{decimal_part}"
        elif '.' in cleaned_price:
            formatted_price = cleaned_price.replace(',', '.')
        else:
            formatted_price = cleaned_price

        try:
            price_value = float(formatted_price)
            price_num = f"€ {price_value:.2f}"
        except (ValueError, TypeError):
            price_num = None

        print(f"💶 Processed price: {price_num}")

        # location
        location = ""
        for text in soup.stripped_strings:
            if any(city in text for city in ["Zuidland", "Rotterdam", "Amsterdam"]):
                location = text.strip()
                break
        print(f"📍 Location: {location}")

        # images
        image_urls = []
        slider = soup.find('ul', class_='slider')
        if slider:
            for img in slider.find_all("img", class_="Carousel-image"):
                src = img.get("src")
                if src and src.startswith("//"):
                    src = "https:" + src
                if src:
                    image_urls.append(src)

        main_image_path = download_image(image_urls[0], title) if image_urls else None
        print(f"🖼️ Images found: {len(image_urls)}")

        # --- Filtration ---
        # Set default values
        exclude_keywords = exclude_keywords or []
        min_price = min_price if min_price is not None else 0
        max_price = max_price if max_price is not None else float('inf')

        print(f"🔍 Filtering: min_price={min_price}, max_price={max_price}, exclude_keywords={exclude_keywords}")

        # check for excluded keywords
        exclude_found = any(
            word.lower() in full_description.lower() or word.lower() in title.lower()
            for word in exclude_keywords
        )
        if exclude_found:
            print(f"❌ Skipping item due to excluded word: {title}")
            return None

        # Check price range
        if price_num:
            try:
                price_value = float(price_num.replace('€ ', ''))
                price_ok = min_price <= price_value <= max_price
                print(f"💰 Price check: {price_value} in range [{min_price}, {max_price}] = {price_ok}")
            except:
                price_ok = False
                print(f"❌ Price parsing failed")
        else:
            price_ok = False
            print(f"❌ No price found")

        if not price_ok:
            print(f"💰 Skipping item due to price: {title} | Price: {price_num}")
            return None

        result = {
            "title": title,
            "full_description": full_description,
            "condition": condition,
            "date": date,
            "price": price_num or "Не указана",
            "location": location,
            "main_image_downloaded": main_image_path,
            "link": url
        }
        print(f"✅ Product parsed successfully: {title} - {price_num}")
        return result

    except Exception as e:
        print(f"❌ Error parsing product page: {e}")
        import traceback
        traceback.print_exc()
        return None


# === Save to SQLite ===
def save_to_sqlite(data):
    # Создаем директорию data если её нет
    import os
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect("data/database.sqlite3")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        full_description TEXT,
        condition TEXT,
        price TEXT,
        date TEXT,
        location TEXT,
        main_image_downloaded TEXT,
        link TEXT UNIQUE
    )
    """)

    try:
        cursor.execute("""
        INSERT INTO products (title, full_description, condition, price, date, location, main_image_downloaded, link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["title"],
            data["full_description"],
            data["condition"],
            data["price"],
            data["date"],
            data["location"],
            data["main_image_downloaded"],
            data["link"]
        ))
        conn.commit()
        print(f'Сохранено: {data["title"]} | Цена: {data["price"]} | Ссылка: {data["link"]}')
    except sqlite3.IntegrityError:
        print(f'Дубликат найден (пропущено): {data["link"]}')
    finally:
        conn.close()


# === Основной запуск ===
if __name__ == "__main__":
    browser = init_browser()
    if not browser:
        print("browser is not running, exiting...")
        exit()

    links = parse_search_page(browser, keyword="iphone 11")

    for link in links:
        print(f"Parsing page: {link}")
        product_data = parse_product_page(browser, link, min_price=100, max_price=200, exclude_keywords=[])
    
        if product_data is not None:
            save_to_sqlite(product_data)
        else:
            print("Skipping item due to filtering criteria")

    print("\nResults saved to database.sqlite3")
    print(f"Total products parsed: {len(links)}")