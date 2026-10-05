FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY cli.py cache-cli ./

# SQLite lives on a volume so the cache survives container restarts.
# Switch to PostgreSQL with: -e CACHE_DATABASE_URL=postgresql+asyncpg://user:pass@host/db
VOLUME ["/data"]
ENV CACHE_DATABASE_URL=sqlite+aiosqlite:////data/cache.db

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
