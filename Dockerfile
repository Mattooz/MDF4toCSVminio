FROM python:3

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/venv

# Create virtual environment
RUN python -m venv /app/venv

# Add virtual environment to PATH
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements file
COPY requirements.txt .

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and resources
COPY main.py .
COPY resources/ ./resources/

# Create directories for temporary files
RUN mkdir -p /app/data

# Expose port for Flask application
EXPOSE 5000

# Set environment variables for MinIO (these will be overridden at runtime)
ENV MINIO_USER=minioadmin \
    MINIO_PSW=minioadmin

# Command to run the application
CMD ["python", "main.py"]