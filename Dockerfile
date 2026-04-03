# =====================================================
# Project Trishul - Docker Configuration
# =====================================================
# Build: docker build -t trishul .
# Run:   docker run -it --rm -e DISCORD_WEBHOOK_URL=... trishul
# =====================================================

FROM golang:1.21-alpine AS tools-builder

# Install security tools from source
RUN apk add --no-cache git && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install -v github.com/lc/gau/v2/cmd/gau@latest

# =====================================================
# Final image
# =====================================================
FROM python:3.11-slim

LABEL maintainer="Project Trishul"
LABEL description="Autonomous EASM & Bug Bounty Platform"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

# Copy Go binaries from builder
COPY --from=tools-builder /go/bin/subfinder /usr/local/bin/
COPY --from=tools-builder /go/bin/httpx /usr/local/bin/httpx-pd
COPY --from=tools-builder /go/bin/nuclei /usr/local/bin/
COPY --from=tools-builder /go/bin/naabu /usr/local/bin/
COPY --from=tools-builder /go/bin/katana /usr/local/bin/
COPY --from=tools-builder /go/bin/gau /usr/local/bin/

# Create app directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY .env.example ./

# Create output directory
RUN mkdir -p reports

# Update Nuclei templates
RUN nuclei -ut || true

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
