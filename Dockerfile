# MicroPAD & MicroREF - Empirical Microservices Architecture Research Package
# Multi-stage build for optimal image size

# ============================================================================
# Stage 1: Builder - Install dependencies and build wheels
# ============================================================================
FROM python:3.11-slim AS builder

# Build argument for PyTorch platform (cpu or cu118 for CUDA 11.8)
ARG TORCH_PLATFORM=cpu

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install PyTorch based on platform argument, then other dependencies
RUN if [ "$TORCH_PLATFORM" = "cpu" ]; then \
        pip install --no-cache-dir --user \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        torch==2.0.1+cpu \
        torchvision==0.15.2+cpu; \
    else \
        pip install --no-cache-dir --user \
        torch==2.0.1 \
        torchvision==0.15.2; \
    fi && \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/$TORCH_PLATFORM \
    pip install --no-cache-dir --user -r requirements.txt && \
    find /root/.local -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true && \
    find /root/.local -name "*.pyc" -delete && \
    find /root/.local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim

# Pass through the build argument
ARG TORCH_PLATFORM=cpu

# Metadata
LABEL maintainer="ceduarte at fe dot up dot pt"
LABEL description="MicroPAD+MicroREF - Empirical Microservices Architecture Research Framework"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Centralize all cache directories to /app/data/model_cache
    HF_HOME=/app/.generated/micropad/model_cache/huggingface \
    TRANSFORMERS_CACHE=/app/.generated/micropad/model_cache/huggingface \
    TORCH_HOME=/app/.generated/micropad/model_cache/torch \
    XDG_CACHE_HOME=/app/.generated/micropad/model_cache \
    PATTERNS_DIR=/app/generated_patterns \
    TARGET_REPO=/app/target_repo

# Create app user (don't run as root)
RUN groupadd -r micropad && useradd -r -g micropad -m -s /bin/bash micropad

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/micropad/.local

# Copy only essential files (source code, config, metadata)
# Data files are mounted via Docker volumes to reduce image size
COPY --chown=micropad:micropad src/ ./src/
COPY --chown=micropad:micropad config/ ./config/
COPY --chown=micropad:micropad pyproject.toml setup.py requirements.txt ./
COPY --chown=micropad:micropad README.md LICENSE ./

# Install the package and cleanup (use extra index to prevent torch upgrade)
RUN PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/$TORCH_PLATFORM \
    pip install --no-cache-dir -e . && \
    find /home/micropad/.local -name "*.pyc" -delete && \
    find /home/micropad/.local -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Entrypoint handles volume permissions and drops to micropad user
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create directories for data persistence and model cache
# All cache paths are centralized under /app/data/model_cache to avoid permission issues
RUN mkdir -p /app/data/vectordb \
             /app/data/model_cache/huggingface \
             /app/data/model_cache/torch \
             /app/data/detection_results \
             /app/logs \
             /app/conversations \
             /home/micropad/.cache \
             /home/micropad/.local

# Set PATH to include user packages when running as micropad
ENV PATH=/home/micropad/.local/bin:$PATH

# Expose port (if running as web service in future)
EXPOSE 8000

# Run entrypoint as root to fix permissions, then drop to micropad
ENTRYPOINT ["/app/entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import micropad, microref; print('OK')" || exit 1

# Documentation for available commands
RUN mkdir -p /app/docs && \
    echo "Available Commands:" > /app/docs/COMMANDS.txt && \
    echo "" >> /app/docs/COMMANDS.txt && \
    echo "MicroPAD Commands (Pattern Detection):" >> /app/docs/COMMANDS.txt && \
    echo "  micropad                 - Run MicroPAD pattern detector" >> /app/docs/COMMANDS.txt && \
    echo "  micropad-seed           - Seed the pattern database" >> /app/docs/COMMANDS.txt && \
    echo "" >> /app/docs/COMMANDS.txt && \
    echo "MicroREF Commands (Repository Collection Pipeline):" >> /app/docs/COMMANDS.txt && \
    echo "  microref-collector      - Collect repository metadata from GitHub Archive" >> /app/docs/COMMANDS.txt && \
    echo "  microref-filter         - Filter repositories based on criteria" >> /app/docs/COMMANDS.txt && \
    echo "  microref-generate-csv   - Generate CSV from filtered repositories" >> /app/docs/COMMANDS.txt && \
    echo "  microref-downloader     - Download filtered repositories" >> /app/docs/COMMANDS.txt && \
    echo "  microref-pattern-gen    - Generate patterns from repositories" >> /app/docs/COMMANDS.txt && \
    echo "" >> /app/docs/COMMANDS.txt && \
    echo "For more information, see /app/README.md" >> /app/docs/COMMANDS.txt

# Default command
CMD ["bash"]
