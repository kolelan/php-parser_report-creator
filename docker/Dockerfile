# Используем официальный образ Python
FROM python:3.10

# Устанавливаем PHP и необходимые зависимости
RUN apt-get update && apt-get install -y \
    php \
    php-cli \
    composer \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем PHP-Parser через composer
RUN composer require nikic/php-parser

# Создаем рабочую директорию
WORKDIR /app


# Указываем команду по умолчанию (может быть переопределена в docker-compose)
CMD ["python", "py_csv_report_creator_final.py", "--help"]