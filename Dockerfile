# PlantScan AI - Production Multi-Stage Containerfile
# Builds a lean, secure, unprivileged runtime for FastAPI + TensorFlow Lite inference

# -------------------------------------------------------------
# Stage 1: Build & Dependency Wheel Cache
# -------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# -------------------------------------------------------------
# Stage 2: Minimal Production Image
# -------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# Install system dependencies required by OpenCV and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PLANTSCAN_ENV=production

# Create non-root system user for security compliance
RUN groupadd -r plantscan && useradd -r -g plantscan -s /bin/false appuser

# Copy application source code and models
COPY backend ./backend
COPY ml ./ml
COPY treatment_database ./treatment_database
COPY datasets/reports ./datasets/reports
COPY config ./config
COPY utils ./utils

# Set ownership
RUN chown -R appuser:plantscan /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
