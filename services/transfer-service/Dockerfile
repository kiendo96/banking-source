FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy common library
COPY common /app/common

# Copy service files
COPY services/transfer-service /app

# Install dependencies
RUN pip install --no-cache-dir -r common/requirements.txt

RUN groupadd -g 1000 appuser && useradd -m -r -u 1000 -g appuser appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
