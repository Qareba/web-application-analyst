#!/bin/bash

# Создаем необходимые директории
mkdir -p data media logs

# Собираем и запускаем Docker контейнер
echo "🐳 Building and starting Docker container..."
docker-compose up --build -d

# Показываем логи
echo "📋 Showing logs..."
docker-compose logs -f 