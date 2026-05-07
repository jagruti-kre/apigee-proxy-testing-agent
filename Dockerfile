FROM python:3.11-slim

WORKDIR /app

# Install build deps required by native packages (chromadb/hnswlib, pdfplumber, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ libffi-dev cmake && \
    rm -rf /var/lib/apt/lists/*

# Stage 1: Install CORE web-server deps (must succeed for /health probe)
COPY requirements-core.txt .
RUN pip install --no-cache-dir --timeout 120 -r requirements-core.txt

# Stage 2: Install remaining deps (agent-specific — tolerate failures)
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 -r requirements.txt || \
    echo "WARNING: Some optional packages failed to install — server will start in degraded mode"

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]