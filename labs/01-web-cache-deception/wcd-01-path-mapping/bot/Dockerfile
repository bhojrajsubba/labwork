FROM python:3.11-slim

WORKDIR /app

# Create non-root user with home directory
RUN groupadd -r botgroup && useradd -m -r -g botgroup botuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R botuser:botgroup /app
USER botuser

EXPOSE 5001

CMD ["python", "bot.py"]
