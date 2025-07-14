from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sys
import os
import requests


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

ALLOWED_CHAT_IDS = set()  # Глобальный список разрешённых chat_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ALLOWED_CHAT_IDS
    try:
        response = requests.get("http://127.0.0.1:5000/get_allowed_chat_ids")
        if response.status_code == 200:
            data = response.json()
            ALLOWED_CHAT_IDS = set(data.get("allowed_chat_ids", []))
            print(f"✅ Updated allowed chat IDs: {ALLOWED_CHAT_IDS}")
        else:
            print("❌ Failed to fetch allowed chat IDs")
    except Exception as e:
        print(f"⚠️ Error fetching chat IDs: {e}")
    if update.effective_chat is not None:
        chat_id = update.effective_chat.id
        if chat_id in ALLOWED_CHAT_IDS:
            chat_ids = context.application.bot_data.setdefault('user_chat_ids', set())
            chat_ids.add(chat_id)
            if update.message:
                await update.message.reply_text('You are subscribed to new products!')
        else:
            if update.message:
                await update.message.reply_text('You do not have permission to use this bot.')
    else:
        if update.message:
            await update.message.reply_text('Error: could not determine chat.')


async def broadcast_new_products(context: ContextTypes.DEFAULT_TYPE):
    global ALLOWED_CHAT_IDS

    sent_links = context.application.bot_data.setdefault('sent_links', set())
    chat_ids = context.application.bot_data.get('user_chat_ids', set())

    try:
        resp = requests.get('http://127.0.0.1:5000/get_new_products')
        if resp.status_code == 200:
            products = resp.json()
            for product in products:
                link = product.get('link')
                if link and link not in sent_links:
                    msg = f"\n<b>{product.get('title')}</b>\nPrice: {product.get('price')}\nDescription: {product.get('full_description')}\nLink: {link}"

                    for chat_id in chat_ids:
                        if chat_id in ALLOWED_CHAT_IDS:
                            try:
                                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML')
                            except Exception as e:
                                print(f"⚠️ Error sending message to {chat_id}: {e}")

                    sent_links.add(link)
    except Exception as e:
        print(f"❌ Error fetching new products: {e}")





def create_bot_app():
    """Создает и настраивает приложение бота"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN is not set in environment variables!")
        exit(1)
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    # Adding task to JobQueue
    if app.job_queue:
        app.job_queue.run_repeating(broadcast_new_products, interval=120, first=5)
    
    return app

# Создаем глобальный экземпляр бота
app = create_bot_app()
