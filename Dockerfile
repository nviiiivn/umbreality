FROM python:3.13-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source (volumes override at runtime for editable paths)
COPY . .

# Default host for Docker — bind to all interfaces
ENV UAI_HOST=0.0.0.0

EXPOSE 8910

CMD ["python", "worker_api.py"]
