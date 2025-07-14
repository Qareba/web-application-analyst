#!/usr/bin/env python3
"""
Главный файл для запуска веб-панели и Telegram бота одновременно
"""

import threading
import time
import sys
import os
from flask import Flask
import subprocess

# Добавляем пути для импорта модулей
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def run_web_app():
    """Запускает веб-приложение Flask"""
    try:
        from web.app import app
        print("🌐 Starting web application...")
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        print(f"❌ Error starting web app: {e}")

def run_telegram_bot():
    """Запускает Telegram бота"""
    try:
        # Импортируем и запускаем бота
        from bot.bot import app as bot_app
        bot_app.run_polling()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

def main():
    """Главная функция для запуска всех сервисов"""
    print("🚀 Starting all services...")
    print("=" * 50)
    
    # Запускаем веб-приложение в отдельном потоке
    web_thread = threading.Thread(target=run_web_app, daemon=True)
    web_thread.start()
    
    # Даем веб-приложению время на запуск
    print("⏳ Waiting for web app to start...")
    time.sleep(3)
    
    # Запускаем бота в основном потоке
    print("🤖 Starting Telegram bot...")
    run_telegram_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        print("✅ All services stopped")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1) 