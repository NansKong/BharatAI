FROM python:3.11-slim

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies (including Playwright deps + PDF tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    libmagic1 \
    poppler-utils \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright Chromium (for dynamic site scraping)
RUN playwright install chromium

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system bharatai && adduser --system --ingroup bharatai bharatai
RUN chown -R bharatai:bharatai /app
USER bharatai

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
