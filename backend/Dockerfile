FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV POETRY_VERSION=2.1.4

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . .
RUN chmod +x /app/scripts/*.sh

EXPOSE 8000

CMD ["sh", "/app/scripts/start-api.sh"]
