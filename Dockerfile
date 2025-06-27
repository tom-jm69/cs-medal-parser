# Multi-stage build for minimal production image
FROM python:3.13.5-alpine AS builder

# Install build dependencies (needed only for building packages)
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Production stage - minimal runtime image
FROM python:3.13.5-alpine AS runtime

# Install only runtime dependencies (much smaller than build deps)
RUN apk add --no-cache \
    jpeg \
    zlib \
    freetype \
    lcms2 \
    openjpeg \
    tiff

# Create app user for security
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application files
COPY config.py .
COPY main.py .
COPY src/ ./src/

# Create data directories and set permissions
RUN mkdir -p data/medals data/responses && \
    chown -R appuser:appgroup /app

# Set Python path to include src directory
ENV PYTHONPATH="${PYTHONPATH}:/app/src"
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Switch to non-root user
USER appuser

# Set default command
CMD ["python3", "-u", "main.py"]
