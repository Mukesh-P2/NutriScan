# NutriScan backend — FastAPI on uvicorn.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as a non-root user. /data holds the SQLite file when DATABASE_URL points there;
# a named volume mounted at /data inherits this ownership on first creation.
RUN useradd --create-home appuser \
    && mkdir -p /data \
    && chown -R appuser /app /data
USER appuser

EXPOSE 8000

# In prod, run migrations first:  alembic upgrade head && uvicorn ...
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
