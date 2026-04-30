FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps for cryptography / Pillow / mysql client
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
        libffi-dev \
        libssl-dev \
        libjpeg-dev \
        zlib1g-dev \
        curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt \
 && pip install gunicorn==21.2.0 eventlet==0.36.1

COPY . .

RUN mkdir -p /app/uploads/profiles

EXPOSE 5000

# Single eventlet worker is required for Flask-SocketIO without a message queue.
CMD ["gunicorn", \
     "-k", "eventlet", \
     "-w", "1", \
     "--bind", "0.0.0.0:5000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "wsgi:app"]
