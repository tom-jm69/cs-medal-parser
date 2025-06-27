FROM python:3.13.5-alpine

# Set working directory
WORKDIR /app

# Install system dependencies in one RUN command to minimize layers
# Copy requirements early to leverage caching for dependencies
COPY requirements.txt requirements.txt

# Install Python dependencies in a single RUN command
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Set default command
CMD ["python3", "-u", "main.py"]
