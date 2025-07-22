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

The application expects a MinIO server to be available at `minio:9000`. You'll need to set-up docker compose, a sample docker compose can be found [here](https://gist.github.com/Mattooz/99c5876133c1da671c377d8095745fa1)

## API Usage

The application exposes a single endpoint:

- POST `/mdf-handle`: Processes MDF files from MinIO and converts them to CSV

## Project Structure

- `main.py`: Main application code
- `requirements.txt`: Python dependencies
- `resources/`: Contains DBC files for CAN bus decoding
- `Dockerfile`: Instructions for building the Docker image

## Environment Variables
For the time being these are the only variables. In the future I plan to add env vars to add DBCs, change port to the webhook, change port or address to the minio server and more, as to have a more configurable application.

- `MINIO_USER`: MinIO access key (default: minioadmin)
- `MINIO_PSW`: MinIO secret key (default: minioadmin)

> **_Nota per il Professore:_**  Il diario dei progressi si trova sempre su questa repo.
