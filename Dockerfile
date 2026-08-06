FROM python:3.12-slim

WORKDIR /app

# Install necessary system libraries for C++ extensions (numpy, chromadb)
RUN apt-get update && apt-get install -y \
    build-essential \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model so it's baked into the image, preventing startup timeouts
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# Copy the rest of the application
COPY . .

# Railway dynamically provides the PORT environment variable
CMD sh -c "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
