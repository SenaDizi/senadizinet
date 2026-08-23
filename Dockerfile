FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     libpq-dev     curl     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000 10000

# Explicitly bind to 0.0.0.0 and dynamically injected $PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
