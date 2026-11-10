# Етап 1: Збірка та встановлення
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
# Копіюємо весь код (включаючи src/)
COPY . .
# Встановлюємо залежності та сам пакет findex
RUN uv sync --frozen --no-dev

# Етап 2: Фінальний образ
FROM python:3.12-slim
WORKDIR /app
# Копіюємо віртуальне середовище
COPY --from=builder /app/.venv /app/.venv
# Копіюємо код (для шаблонів та індексу)
COPY . .
# Встановлюємо пакет findex у віртуальне середовище (використовуючи uv pip)
RUN /app/.venv/bin/python -m ensurepip --upgrade && /app/.venv/bin/python -m pip install --no-cache-dir --no-deps -e .
# Створюємо користувача
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Додаємо віртуальне середовище в PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV INDEX_PATH="/app/index.bin"

EXPOSE 8000
CMD ["findex", "serve", "--port", "8000", "--workers", "1"]