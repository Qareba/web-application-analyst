from flask import Flask, render_template, request, jsonify, url_for
import threading
import time
import sqlite3

# === Твой парсер ===
from parser.parser_marketplays import parse_search_page, parse_product_page, save_to_sqlite, init_browser

app = Flask(__name__, static_folder='static')

# === Global Variables ===
parser_config = {
    "running": False,
    "interval": 300,  # 5 minutes
    "keyword": "iphone 11",
    "min_price": 100,
    "max_price": 200,
    "exclude_keywords": ["broken", "defect"],
    "last_run": None,
    "new_products": []
}
ALLOWED_USER_IDS = set()

# Глобальная переменная для хранения активного таймера
active_timer = None

# === Function to run the parser ===
def run_parser():
    global active_timer
    
    print("🔧 run_parser() function called")
    print(f"📊 Parser config at start: {parser_config}")
    
    if not parser_config["running"]:
        print("🛑 Parser stopped by user")
        return

    print("🔄 Starting parsing...")
    print(f"📊 Config: keyword='{parser_config['keyword']}', min_price={parser_config['min_price']}, max_price={parser_config['max_price']}")

    print("🔧 Calling init_browser()...")
    driver = init_browser()
    print(f"🔧 Browser result: {driver}")
    if not driver:
        print("❌ Failed to start browser")
        return

    try:
        print("🔍 Searching for products...")
        links = parse_search_page(driver, keyword=parser_config["keyword"], max_pages=3)
        print(f"📋 Found {len(links)} links to parse")
        
        # Проверяем статус running после получения ссылок
        if not parser_config["running"]:
            print("🛑 Parsing stopped by user")
            return
            
        for i, link in enumerate(links, 1):
            # Проверяем статус running перед каждым парсингом
            if not parser_config["running"]:
                print("🛑 Parsing stopped by user")
                return
                
            print(f"🔗 Parsing link {i}/{len(links)}: {link}")
            product_data = parse_product_page(
                driver, link,
                min_price=parser_config["min_price"],
                max_price=parser_config["max_price"],
                exclude_keywords=parser_config["exclude_keywords"]
            )
            print(f"📦 Parsing result: {product_data}")
            if product_data:
                print(f"✅ Product found: {product_data.get('title')} - {product_data.get('price')}")
                # Проверяем, есть ли такой товар в БД
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
                cursor.execute("SELECT * FROM products WHERE link=?", (link,))
                exists = cursor.fetchone()
                conn.close()

                if not exists:
                    save_to_sqlite(product_data)
                    print(f"💾 Saved to database: {product_data.get('title')}")
                    parser_config["new_products"].append({
                        "title": product_data.get("title"),
                        "price": product_data.get("price"),
                        "full_description": product_data.get("full_description"),
                        "link": product_data.get("link"),
                    })
                else:
                    print(f"⏭️ Product already exists in database: {product_data.get('title')}")
            else:
                print(f"❌ No product data returned for link {i}")

        # Проверяем статус running перед финальной обработкой
        if not parser_config["running"]:
            print("🛑 Parsing stopped by user")
            return
            
        parser_config["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"✅ Parsing completed. New products: {len(parser_config['new_products'])}")
        print(f"📅 Last run: {parser_config['last_run']}")
        parser_config['new_products'] = []

    except Exception as e:
        print(f"❌ Parsing error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🧹 Closing browser...")
        driver.quit()

    # Restart after N seconds only if still running
    if parser_config["running"]:
        print(f"⏰ Scheduling next run in {parser_config['interval']} seconds...")
        active_timer = threading.Timer(parser_config["interval"], run_parser)
        active_timer.start()
    else:
        print("🛑 Parser stopped, not scheduling next run")


# === API for starting/stopping the parser ===
@app.route("/toggle_parser", methods=["POST"])
def toggle_parser():
    global active_timer
    action = request.form.get("action")  # or request.values.get("action")
    print(f"🎛️ Toggle parser called with action: {action}")
    print(f"📊 Current parser status: {parser_config['running']}")
    
    if action == "start" and not parser_config["running"]:
        print("🚀 Starting parser...")
        parser_config["running"] = True
        parser_config["new_products"] = []
        print(f"📊 Parser config after start: {parser_config}")
        print("🔧 Calling run_parser()...")
        run_parser()
        print("✅ run_parser() called successfully")
    elif action == "stop":
        print("🛑 Stopping parser...")
        parser_config["running"] = False
        # Отменяем активный таймер если он есть
        if active_timer and active_timer.is_alive():
            active_timer.cancel()
            active_timer = None
            print("⏹️ Timer cancelled")
        print(f"📊 Parser status: {'Running' if parser_config['running'] else 'Stopped'}")
    else:
        print(f"⚠️ Invalid action '{action}' or parser already {'running' if parser_config['running'] else 'stopped'}")
    
    print(f"📊 Final parser status: {parser_config['running']}")
    return jsonify({"status": parser_config["running"]})

@app.route("/chat_ids")
def chat_ids_admin():
    return render_template("chat_ids.html", allowed_chat_ids=",".join(map(str, ALLOWED_USER_IDS)))

@app.route("/get_allowed_chat_ids")
def get_allowed_chat_ids():
    return jsonify({"allowed_chat_ids": list(ALLOWED_USER_IDS)})

# === API for updating configuration ===
@app.route("/update_config", methods=["POST"])
def update_config():
    data = request.form
    parser_config["keyword"] = data.get("keyword", parser_config["keyword"])
    parser_config["min_price"] = float(data.get("min_price", parser_config["min_price"]))
    parser_config["max_price"] = float(data.get("max_price", parser_config["max_price"]))
    exclude_input = data.get("exclude_keywords", "")
    parser_config["exclude_keywords"] = [w.strip() for w in exclude_input.split(",")] if exclude_input else []
    return jsonify({"status": "ok"})

@app.route("/admin/chat_ids/update", methods=["POST"])
def update_allowed_chat_ids():
    global ALLOWED_USER_IDS
    chat_ids_str = request.form.get("chat_ids", "")
    # Парсим строку в список chat_id
    chat_ids = [int(cid.strip()) for cid in chat_ids_str.split(",") if cid.strip().isdigit()]
    ALLOWED_USER_IDS = set(chat_ids)
    print(f"✅ ALLOWED_CHAT_IDS updated to: {ALLOWED_USER_IDS}")
    return jsonify({"status": "ok", "allowed_chat_ids": list(ALLOWED_USER_IDS)})


# === Main Page ===
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/debug")
def debug():
    return render_template("debug.html")


# === Results Page ===
@app.route("/results")
def results():
    conn = sqlite3.connect("data/database.sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    columns = ["ID", "Название", "Описание", "Состояние", "Цена", "Дата", "Местоположение", "Изображение", "Ссылка"]
    return render_template("results.html", data=rows, columns=columns)


# === Get new products ===
@app.route("/get_new_products")
def get_new_products():
    return jsonify(parser_config["new_products"])

@app.route("/results_info")
def results_info():
    return jsonify({
        "last_run": parser_config["last_run"],
        "product_count": len(parser_config["new_products"]),
    })

@app.route("/parser_status")
def parser_status():
    """Детальный статус парсера"""
    return jsonify({
        "running": parser_config["running"],
        "last_run": parser_config["last_run"],
        "keyword": parser_config["keyword"],
        "min_price": parser_config["min_price"],
        "max_price": parser_config["max_price"],
        "exclude_keywords": parser_config["exclude_keywords"],
        "interval": parser_config["interval"],
        "new_products_count": len(parser_config["new_products"]),
        "new_products": parser_config["new_products"]
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)