FROM python:3.13.5-alpine

# Set working directory
WORKDIR /app

# Install system dependencies needed for Pillow and other packages
RUN apk add --no-cache \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    gcc \
    musl-dev

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY config.py .
COPY main.py .
COPY src/ ./src/

# Create data directories
RUN mkdir -p data/medals data/responses

# Set Python path to include src directory (alternative to sys.path modification)
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Set default command
CMD ["python3", "-u", "main.py"]
