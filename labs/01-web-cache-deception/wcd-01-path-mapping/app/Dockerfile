FROM python:3.11-slim

WORKDIR /app

# Create non-root user with home directory
RUN groupadd -r appgroup && useradd -m -r -g appgroup appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure appuser owns the application files
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "app:app"]
