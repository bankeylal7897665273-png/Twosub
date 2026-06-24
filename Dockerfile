# Base image Python 3.9
FROM python:3.9-slim

# Node, Surge aur pexpect ke liye zaroori tools install karna
RUN apt-get update && apt-get install -y curl unzip expect nodejs npm \
    && npm install -global surge \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements copy aur install karna
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pura code copy karna
COPY . .

# Hugging Face ke liye port 7860 expose karna
EXPOSE 7860

# API start karne ka command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
