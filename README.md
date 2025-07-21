# MDF4 to CSV Converter with MinIO Integration

This application processes MDF4 files, extracts data using CAN bus logging, and converts them to CSV format. It integrates with MinIO for object storage.

## Docker Setup

### Building the Docker Image

To build the Docker image, run the following command from the project root directory:

```bash
docker build -t mdf4-to-csv .
```

### Running the Docker Container

To run the container with default MinIO credentials:

```bash
docker run -p 5000:5000 mdf4-to-csv
```

To override the MinIO credentials:

```bash
docker run -p 5000:5000 -e MINIO_USER=your_access_key -e MINIO_PSW=your_secret_key mdf4-to-csv
```

### Connecting to a MinIO Server

The application expects a MinIO server to be available at `minio:9000`. You can use Docker Compose to set up both services together, or modify the endpoint in the application code.

## API Usage

The application exposes a single endpoint:

- POST `/mdf-handle`: Processes MDF files from MinIO and converts them to CSV

## Project Structure

- `main.py`: Main application code
- `requirements.txt`: Python dependencies
- `resources/`: Contains DBC files for CAN bus decoding
- `Dockerfile`: Instructions for building the Docker image

## Dependencies

The Dockerfile installs the following build dependencies to support the compilation of C extensions required by asammdf:
- build-essential
- gcc
- g++
- cmake
- git

Additionally, the Dockerfile clones the libdeflate repository to ensure it's available during the build process. This is necessary because asammdf or one of its dependencies requires libdeflate for compression functionality.

These dependencies and steps are necessary for the proper installation of asammdf and its requirements.

## Environment Variables

- `MINIO_USER`: MinIO access key (default: minioadmin)
- `MINIO_PSW`: MinIO secret key (default: minioadmin)