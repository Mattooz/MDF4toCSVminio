> **_Nota per il Professore:_**  Il diario dei progressi si trova sempre su questa repo. Il file è 'progress.txt'.

# MDF4 to CSV Converter with MinIO Integration

This application processes MDF4 files, extracts data using CAN bus logging, and converts them to CSV format. It integrates with MinIO for object storage.
It only has one DBC file, so it is quite basic at the moment. I plan to add more and a way to add custom one via environment variables.

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

The application expects a MinIO server to be available at `minio:9000`. Therefor, you'll need to set-up docker compose. A sample compose.yaml can be found [here](https://gist.github.com/Mattooz/99c5876133c1da671c377d8095745fa1).

## API Usage

The application exposes a single endpoint:

- POST `/mdf-handle`: Processes MDF files from MinIO and converts them to CSV

## Project Structure

- `main.py`: Main application code
- `requirements.txt`: Python dependencies
- `resources/`: Contains DBC files for CAN bus decoding
- `Dockerfile`: Instructions for building the Docker image

## Environment Variables
At the moment, there are the only variables available, but in the future I plan to add more.

- `MINIO_USER`: MinIO access key (default: minioadmin)
- `MINIO_PSW`: MinIO secret key (default: minioadmin)
