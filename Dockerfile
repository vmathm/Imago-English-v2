# Dockerfile (root)
FROM python:3.10-slim

# Set working directory to /app (matches your repo structure)
WORKDIR /app

# Create SQLite data directory
RUN mkdir -p /app/instance

# Set default DB path (SQLite)
ENV DATABASE_URL=sqlite:////app/instance/app.db

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 5000

# Run Flask
CMD sh -c "gunicorn -b 0.0.0.0:${PORT:-8080} main:app"