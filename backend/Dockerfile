FROM python:3.11-slim

# ─── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libpq-dev \
    gcc \
    g++ \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# ─── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ─── Python dependencies ──────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─── Application code ─────────────────────────────────────────────────────────
COPY . .

# ─── Entrypoint permissions ───────────────────────────────────────────────────
RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
