FROM python:3.12-slim

# System dependencies for ffmpeg, audio processing, and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    patchelf \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && ln -sf "$(which node || which nodejs)" /usr/local/bin/node 2>/dev/null || true \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
# Install CPU-only torch first to avoid pulling the 2GB+ CUDA build
COPY requirements.txt .
RUN pip install --no-cache-dir \
    torch==2.5.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade yt-dlp \
    && pip install --no-cache-dir yt-dlp-ejs \
    && find /usr/local/lib -name "*.so*" -exec patchelf --clear-execstack {} \; 2>/dev/null || true

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p output/jobs

EXPOSE 8000

COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
