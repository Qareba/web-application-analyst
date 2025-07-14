# Parser and Bot Launcher

This project includes a web panel for product parsing and a Telegram bot for notifications.

## Quick Start

### Linux/Mac
```bash
./start.sh
```

### Windows
```cmd
start.bat
```

### Manual Launch
```bash
# Activate the virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows

# Start all services
python main.py
```

## What is Launched

1. **Web Panel** - available at http://localhost:5000
   - Configure parsing parameters
   - Start/stop the parser
   - View results

2. **Telegram Bot** - automatically sends notifications about new products
   - `/start` command to subscribe to notifications
   - Checks for new products every 2 minutes

## Project Structure

```
bot_test/
├── main.py          # Main entry point
├── start.sh         # Launch script for Linux/Mac
├── start.bat        # Launch script for Windows
├── web/             # Web application
│   ├── app.py       # Flask app
│   ├── templates/   # HTML templates
│   └── static/      # CSS styles
├── bot/             # Telegram bot
│   └── bot.py       # Bot code
├── parser/          # Parser
│   └── parser_marketplays.py
└── venv/            # Virtual environment
```

## Requirements

- Python 3.8+
- Dependencies installed in venv
- Internet access for parsing and Telegram API

## Stopping

Press `Ctrl+C` to stop all services. 