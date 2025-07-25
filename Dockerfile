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
COPY resources/config.toml ./resources/

# default volume for dbc files
VOLUME /dbc

# Copy DBC file to the volume
COPY resources/11-bit-OBD2-v4.0.dbc /dbc/

# Create directories for temporary files
RUN mkdir -p /app/data

# Expose port for Flask application
EXPOSE 5000/tcp
EXPOSE 5000/udp

# Set environment variables for MinIO (these will be overridden at runtime)
ENV MINIO_USER=minioadmin \
    MINIO_PSW=minioadmin \
    MINIO_URL=minio:9000 \
    CONFIG_PATH=resources/config.toml \
    CONFIG_VOLUME=resources \
    DBC_VOLUME=/dbc

# Command to run the application
CMD ["python", "main.py"]