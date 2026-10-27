# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5213 \
    HOST=0.0.0.0

# Set working directory
WORKDIR /app

# Copy dependency definition first for Docker layer caching
COPY requirements.txt .

# Install dependencies using pre-built binary wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and default data
COPY data_loader.py graph_builder.py search_engine.py main.py ./
COPY data/ ./data/
COPY link.txt ./link.txt

# Expose API port
EXPOSE 5213

# Healthcheck to verify FastAPI responsiveness
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5213/docs')" || exit 1

# Start FastAPI application with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5213"]
