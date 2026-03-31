# ── Build stage: import CSV data into SQLite ──────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy only what the importer needs
COPY data/             /build/data/
COPY leetcode-browser/import_data.py /build/import_data.py

# Build the database once at image-build time
RUN python import_data.py \
      --data-dir /build/data \
      --db-path  /build/leetcode.db

# ── Runtime stage: lean image with just the app + DB ─────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY leetcode-browser/app.py /app/app.py
COPY --from=builder /build/leetcode.db /app/leetcode.db

EXPOSE 8000

# 0.0.0.0 required so traffic reaches the container from the host
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "8000", "--db-path", "/app/leetcode.db"]
