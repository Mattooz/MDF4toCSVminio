# MDF4 to CSV Converter with MinIO Integration

> **_Nota per il Professore:_**  Il diario dei progressi si trova sempre su questa repo. Il file è 'progress.txt'.

This application processes MDF4 files, extracts data using CAN bus logging, and converts them to CSV format. It integrates with MinIO for object storage.

## Overview

The MDF4 to CSV Converter is designed to run as a service within containerized environments like Docker Compose. It monitors a MinIO bucket for new MDF4 files, processes them using CAN bus decoding with DBC files, and outputs CSV files to another MinIO bucket.

Key features include:
- Processing MDF4 files and converting them to CSV format
- Integration with MinIO for object storage
- Support for multiple DBC files for CAN bus decoding
- Channel-specific DBC file assignment
- Automatic downloading of DBC files from URLs
- Fallback to default DBC file if no configuration is found

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

#### Configuration File Format

The configuration file uses the TOML format and supports the following options:

```toml
# Define DBC file sources
[[dbc.src]]
filepath = 'path/to/first/dbc/file.dbc'  # Path relative to DBC_VOLUME
can_bus_channel = 0                      # Specific CAN bus channel (or 'all' for all channels)
origin = 'http://example.com/dbc/file'   # Optional URL to download the DBC file

# You can define multiple DBC files
[[dbc.src]]
filepath = 'path/to/second/dbc/file.dbc'
can_bus_channel = 'all'                  # This DBC file will be used for all channels
```

#### DBC File Configuration Options

Each DBC file entry supports the following options:

- `filepath`: Path to the DBC file, relative to the DBC volume
- `can_bus_channel`: The CAN bus channel this DBC file should be used for
  - Set to a number (e.g., `0`, `1`, `9`) to use for a specific channel
  - Set to `'all'` to use for all channels
- `origin`: (Optional) URL to download the DBC file from if it doesn't exist

#### Automatic DBC File Download

If you specify an `origin` URL for a DBC file, the application will automatically download the file if it doesn't exist in the DBC volume. This is useful for keeping DBC files up-to-date or for deploying the application without having to manually copy DBC files.

#### Default Configuration

If no configuration file exists, the application will copy the default configuration, which uses the default DBC file (11-bit-OBD2-v4.0.dbc) for channel 0.

#### Example Configurations

**Basic configuration with one DBC file:**
```toml
[[dbc.src]]
filepath = '11-bit-OBD2-v4.0.dbc'
can_bus_channel = 0
```

**Configuration with multiple DBC files for different channels:**
```toml
[[dbc.src]]
filepath = '11-bit-OBD2-v4.0.dbc'
can_bus_channel = 0

[[dbc.src]]
filepath = 'custom-protocol.dbc'
can_bus_channel = 9
```

**Configuration with automatic download:**
```toml
[[dbc.src]]
filepath = 'latest-obd2.dbc'
can_bus_channel = 'all'
origin = 'https://example.com/dbc/latest-obd2.dbc'
```


## API Usage

The application exposes a single endpoint:

- POST `/mdf-handle`: Processes MDF files from MinIO and converts them to CSV

This endpoint is typically triggered by MinIO notifications when new files are uploaded.

## Project Structure

- `main.py`: Main application code
- `requirements.txt`: Python dependencies
- `resources/`: Contains default configuration and DBC files
- `Dockerfile`: Instructions for building the Docker image

## Application Workflow

The application follows this workflow when it starts and processes files:

### Initialization

1. **Default File Management**: The application checks if the configuration file and default DBC file exist in their respective volumes. If they don't exist, it copies the default files from the resources directory.

2. **Configuration Loading**: The application loads the configuration file using the TOML parser.

3. **DBC File Download**: If any DBC files in the configuration have an `origin` URL, the application downloads them if they don't already exist in the DBC volume.

4. **Server Start**: The Flask server starts and listens for incoming requests.

### File Processing

When a file is uploaded to MinIO and the `/mdf-handle` endpoint is triggered:

1. **File Retrieval**: The application retrieves the MDF file from MinIO.

2. **DBC File Selection**: Based on the configuration, the application selects the appropriate DBC files for each CAN bus channel.

3. **Data Extraction**: The application uses the asammdf library to extract data from the MDF file using the selected DBC files.

4. **CSV Export**: The extracted data is exported to a CSV file.

5. **Upload to MinIO**: The CSV file is uploaded to the output bucket in MinIO.

### Multiple DBC File Handling

The application supports using different DBC files for different CAN bus channels:

- If a DBC file is configured for a specific channel (e.g., `can_bus_channel = 0`), it will only be used for that channel.
- If a DBC file is configured for all channels (e.g., `can_bus_channel = 'all'`), it will be used for all channels.
- If multiple DBC files are configured for the same channel, all of them will be used.

This allows for flexible decoding of CAN bus data from different sources or protocols.

## Environment Variables

The application uses the following environment variables:

- `MINIO_USER`: MinIO access key (default: minioadmin)
- `MINIO_PSW`: MinIO secret key (default: minioadmin)
- `MINIO_URL`: MinIO server URL (default: minio:9000)
- `CONFIG_PATH`: Path to the configuration file (default: /data/config.toml)
- `CONFIG_VOLUME`: Volume where configuration is stored (default: /data)
- `DBC_VOLUME`: Volume where DBC files are stored (default: /dbc)
