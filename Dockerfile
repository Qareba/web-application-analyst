# Используем официальный образ Python
FROM python:3.12-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Создаем виртуальное окружение
RUN python -m venv /opt/venv

# Добавляем бинарные файлы виртуального окружения в PATH
ENV PATH="/opt/venv/bin:$PATH"

# Устанавливаем зависимости в виртуальное окружение
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем директорию для медиа файлов
RUN mkdir -p media

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порт для веб-приложения
EXPOSE 5000

# Запускаем приложение
CMD ["python", "main.py"]