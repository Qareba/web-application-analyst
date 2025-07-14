# Docker Setup for Telegram Bot and Web Parser

This project now supports running in a Docker container.

## 🐳 Quick Start

### 1. Build and Run
```bash
# Create directories for data
mkdir -p data media logs

# Start with docker-compose
docker-compose up --build -d

# Or use the ready-made script
./docker-run.sh
```

### 2. View Logs
```bash
# Show logs
docker-compose logs -f

# Show logs for a specific service
docker-compose logs -f bot-app
```

### 3. Stop
```bash
docker-compose down
```

## 📁 Data Structure

After launch, the following directories will appear in the project root:
- `data/` - SQLite database
- `media/` - uploaded images
- `logs/` - application logs

## 🔧 Configuration

### Environment Variables
In `docker-compose.yml` you can configure:
- `TELEGRAM_BOT_TOKEN` - your Telegram bot token
- `FLASK_ENV` - Flask environment (production/development)

### Ports
- `5000` - web interface (http://localhost:5000)

## 🛠️ Development

### Manual Image Build
```bash
docker build -t bot-app .
```

### Manual Container Run
```bash
docker run -p 5000:5000 -v $(pwd)/data:/app/data -v $(pwd)/media:/app/media bot-app
```

## 🔍 Debugging

### Enter the Container
```bash
docker-compose exec bot-app bash
```

### View Files in the Container
```bash
docker-compose exec bot-app ls -la
```

## 📊 Monitoring

### Container Status
```bash
docker-compose ps
```

### Resource Usage
```bash
docker stats
```

## 🚨 Troubleshooting

### If Chrome does not start
The container is configured to work with Chrome in headless mode. If you encounter issues:
1. Check the logs: `docker-compose logs bot-app`
2. Make sure the container has enough memory (2GB+)

### If the database is not created
1. Check permissions for the `data/` directory
2. Make sure the directory exists: `mkdir -p data`

### If the web interface is unavailable
1. Check that port 5000 is not in use: `netstat -tulpn | grep 5000`
2. Check Flask logs: `docker-compose logs bot-app`

## 🔄 Update

### Rebuild with Changes
```bash
docker-compose down
docker-compose up --build -d
```

### Cleanup
```bash
# Remove containers and images
docker-compose down --rmi all

# Remove all data (careful!)
docker-compose down -v
rm -rf data media logs
```

## 📝 Notes

- All data is saved in the `data/`, `media/`, `logs/` directories
- Chrome runs in headless mode for parsing
- The Telegram bot automatically starts together with the web interface
- The application automatically restarts on failures 