FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for torch
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the custom Flan-T5 model during build
RUN python -c "from transformers import AutoTokenizer, AutoModelForSeq2SeqLM; \
    AutoTokenizer.from_pretrained('5unnySunny/medical-flan-t5-small-log-summarizer'); \
    AutoModelForSeq2SeqLM.from_pretrained('5unnySunny/medical-flan-t5-small-log-summarizer')" || true

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment settings
ENV MODEL_NAME=5unnySunny/medical-flan-t5-small-log-summarizer
ENV MODEL_VERSION=1.0.0
ENV OMP_NUM_THREADS=2
ENV OPENBLAS_NUM_THREADS=1

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8003/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
