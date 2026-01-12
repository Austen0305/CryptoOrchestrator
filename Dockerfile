# Use official Python 3.11 full image for better compatibility with DS libraries
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies (build-essential for compiling some python libs if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server application code
COPY server_fastapi/ ./server_fastapi/

# Expose port (Cloud Run defaults to 8080, but we use 8000 in compose)
EXPOSE 8000

# Set Python path to include root
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "server_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
