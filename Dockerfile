# ====================================================
# Multi-stage Dockerfile
# Stage 1: Builder — install deps
# Stage 2: Runtime — lean image
# ====================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# System dependencies for PDF parsing, lxml, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ====================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Non-root user for security with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# System libs needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application source
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Create writable dirs and user home configuration
RUN mkdir -p data/chroma_db data/raw_pdfs data/raw_html \
    && chown -R appuser:appuser /app /home/appuser

USER appuser

ENV HOME=/home/appuser
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

