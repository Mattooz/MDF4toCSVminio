from fileinput import filename
from typing import Literal

from asammdf import MDF
import os
from flask import Flask, request
from minio import Minio
import re
import toml

APP             = Flask(__name__)
MINIO           = Minio(endpoint=os.environ['MINIO_URL'], access_key=os.environ['MINIO_USER'], secret_key=os.environ['MINIO_PSW'],
                    secure=False)
TMP_FOLDER      = os.path.join('.', 'tmp')
OUTPUT_BUCKET   = 'output'

CONFIG_VOLUME      = os.environ['CONFIG_VOLUME']
DBC_CONFIG_PATH    = os.environ['CONFIG_PATH']

DATA = {}

@APP.route(rule='/mdf-handle', methods=['POST'])
def handle():
    event = request.json

    try:
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            obj = record['s3']['object']['key']

            APP.logger.info(f"Processing new file! Bucket: '{bucket}', File: '{obj}'.")

            mdf_in_path = get_mdf_path(obj, 'input')
            name = basename(obj)
            mdf_out_path = get_mdf_path(name, 'output', 'csv')

            MINIO.fget_object(bucket, obj, mdf_in_path)

            with open(mdf_in_path, 'rb+') as mdf_in_file, MDF(mdf_in_file) as mdf_in:
                handle_mdf(mdf_in, name)

            MINIO.fput_object(OUTPUT_BUCKET, os.path.basename(mdf_out_path), mdf_out_path)

            APP.logger.info(f"Done processing! Uploaded file '{mdf_out_path}' to bucket '{OUTPUT_BUCKET}'")
    except Exception as e:
        APP.logger.error(f'Some went wrong: {e}')

    return '', 200


def handle_mdf(mdf: MDF, name: str):
    config = DATA['config'] if 'config' in DATA else None
    if config is None:
        APP.logger.warning("No config found, using default DBC file")
    dbc_volume = config['dbc']['volume'] if config and 'dbc' in config and 'volume' in config['dbc'] else '/dbc'
    dbc_files = []
    
    if config and 'dbc' in config and 'src' in config['dbc']:
        for dbc_src in config['dbc']['src']:
            dbc_files.append((os.path.join(dbc_volume, dbc_src['filepath']), dbc_src['can_bus_channel']))
    else:
        # Fallback to default DBC file in /dbc volume
        dbc_files.append((os.path.join('/dbc', '11-bit-OBD2-v4.0.dbc'), 0))
    
    decoded = mdf.extract_bus_logging(
        database_files={
            "CAN": dbc_files
        }
    )

    path = get_mdf_path(name, 'output')
    decoded.export(fmt='csv', filename=path, single_time_base=True, delimiter=',', quotechar='"', escapechar='\\')


def get_mdf_path(file_name: str, io: Literal['input', 'output'], extension: Literal['csv', 'mdf', None] = None):
    if io == 'input':
        return os.path.join(TMP_FOLDER, 'mdf_in_' + file_name)
    elif io == 'output':
        if extension is not None:
            return os.path.join(TMP_FOLDER, 'mdf_out_' + file_name + '.' + extension)
        else:
            return os.path.join(TMP_FOLDER, 'mdf_out_' + file_name)
    else:
        raise Exception("Invalid IO id")

def basename(path):
    rgx = r'^(.+?)(?:\.[^.]+)?$'
    return re.match(rgx, path).group(1)

def setup():
    os.makedirs(TMP_FOLDER, exist_ok=True)

def fetch_config():
    with open(DBC_CONFIG_PATH, 'r') as f:
        DATA['config'] = toml.load(f)

def get_config():
    return DATA.get('config')


def copy_default_config(config_path):
    if os.path.exists(config_path):
        APP.logger.info(f"Configuration file found at {config_path}")
        return True
    
    default_config_path = os.path.join('resources', 'config.toml')
    if os.path.exists(default_config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(default_config_path, 'r') as src, open(config_path, 'w') as dst:
            dst.write(src.read())
        
        APP.logger.info(f"Default configuration copied to {config_path}")
        return True
    else:
        APP.logger.error(f"Default configuration not found at {default_config_path}")
        return False


if __name__ == '__main__':
    if not copy_default_config(DBC_CONFIG_PATH):
        raise Exception(f"Failed to find or create configuration at {DBC_CONFIG_PATH}")

    fetch_config()

    APP.run(host='0.0.0.0', port=5000, debug=True)
    APP.logger.info("Server started")
