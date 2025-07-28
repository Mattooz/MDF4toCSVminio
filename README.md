# MDF4 to CSV Converter with MinIO Integration

> **_Nota per il Professore:_**  Il diario dei progressi si trova sempre su questa repo. Il file è 'progress.txt'.

This application processes MDF4 files, extracts data using CAN bus logging, and converts them to CSV format. It integrates with MinIO for object storage.

## Overview

The MDF4 to CSV Converter is designed to run as a service within containerized environments like Docker Compose. It monitors a MinIO bucket for new MDF4 files, processes them using CAN bus decoding with DBC files, and outputs CSV files to another MinIO bucket.

Currently, the application includes one default DBC file (11-bit-OBD2-v4.0.dbc) for CAN bus decoding, with plans to support additional DBC files in future releases.

## Docker Compose Integration

### Sample Docker Compose Configuration

```yaml
version: '3'

services:
  mdf4-to-csv:
    image: mdf4-to-csv:latest
    environment:
      - MINIO_USER=minioadmin
      - MINIO_PSW=minioadmin
      - MINIO_URL=minio:9000
      - CONFIG_PATH=/data/config.toml
      - CONFIG_VOLUME=/data
      - DBC_VOLUME=/dbc
    volumes:
      - dbc-volume:/dbc
      - config-volume:/data
    ports:
      - "5000:5000"
    depends_on:
      - minio
    networks:
      - app-network

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio-data:/data
    networks:
      - app-network

volumes:
  minio-data:
  dbc-volume:
  config-volume:

networks:
  app-network:
```

### Configuration

The application uses a configuration file (`config.toml`) to specify DBC file locations and other settings. If no configuration file exists at the specified path, the application will automatically copy the default configuration.

Similarly, if no DBC file exists in the DBC volume, the application will copy the default DBC file.


## API Usage

The application exposes a single endpoint:

- POST `/mdf-handle`: Processes MDF files from MinIO and converts them to CSV

This endpoint is typically triggered by MinIO notifications when new files are uploaded.

## Project Structure

- `main.py`: Main application code
- `requirements.txt`: Python dependencies
- `resources/`: Contains default configuration and DBC files
- `Dockerfile`: Instructions for building the Docker image

## Environment Variables

The application uses the following environment variables:

- `MINIO_USER`: MinIO access key (default: minioadmin)
- `MINIO_PSW`: MinIO secret key (default: minioadmin)
- `MINIO_URL`: MinIO server URL (default: minio:9000)
- `CONFIG_PATH`: Path to the configuration file (default: /data/config.toml)
- `CONFIG_VOLUME`: Volume where configuration is stored (default: /data)
- `DBC_VOLUME`: Volume where DBC files are stored (default: /dbc)
