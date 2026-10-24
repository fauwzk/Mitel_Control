FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

# iputils-ping / net-tools : nécessaires à "Auto-Fetch MAC" (ping + arp)
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py mitel_core.py endpoints.json ./
COPY static ./static

VOLUME ["/data"]
EXPOSE 8000

# Un seul worker : l'inventaire est un fichier JSON protégé par un verrou en mémoire
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--timeout", "60", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "app:app"]
