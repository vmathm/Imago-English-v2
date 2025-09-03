# Dockerfile (at repo root)

# 1) Base image with Python 3.10, lean Debian
FROM python:3.10-slim

# 2) Create a working directory inside the image
WORKDIR /app

# 3) OS packages (keep minimal; combine in one RUN for layer efficiency)
# - build-essential only if your pip wheels need compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* 

# 4) Install Python deps separately for better caching
#    Copy only requirements first so Docker can cache `pip install`
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Now copy your app code
COPY . .

# 6) Document the port the app uses
EXPOSE 5000

# 7) Default command (dev server)
CMD ["flask", "run"]
