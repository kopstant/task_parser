FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY poetry.lock pyproject.toml ./

# Устанавливаем Poetry и зависимости
RUN python -m pip install --no-cache-dir poetry && \
    apt-get update && \
    apt-get install -y gcc libpq-dev && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root && \
    apt-get remove -y gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем весь проект
COPY . .

ENV PYTHONPATH=/app

# Запускаем
CMD ["python", "-m", "src.bot.main"]