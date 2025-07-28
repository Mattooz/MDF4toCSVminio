from fileinput import filename
from typing import Literal

from asammdf import MDF
import os
from flask import Flask, request
from minio import Minio
import re
import requests
import toml

APP = Flask(__name__)
MINIO = Minio(endpoint=os.environ['MINIO_URL'], access_key=os.environ['MINIO_USER'], secret_key=os.environ['MINIO_PSW'],
              secure=False)
TMP_FOLDER = os.path.join('.', 'tmp')
OUTPUT_BUCKET = 'output'

DEFAULT_CONFIG_PATH = os.path.join('resources', 'config.toml')
DEFAULT_DBC_PATH = os.path.join('resources', '11-bit-OBD2-v4.0.dbc')

DBC_VOLUME = os.environ['DBC_VOLUME']

CONFIG_VOLUME = os.environ['CONFIG_VOLUME']
CONFIG_PATH = os.environ['CONFIG_PATH']

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

            if os.path.exists(mdf_out_path):
                os.remove(mdf_out_path)

            if os.path.exists(mdf_in_path):
                os.remove(mdf_in_path)

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
    dbc_files = []

    if config and 'dbc' in config and 'src' in config['dbc']:
        for dbc_src in config['dbc']['src']:
            if dbc_src['can_bus_channel'] == 'all':
                dbc_files.append((os.path.join(DBC_VOLUME, dbc_src['filepath']), None))
            else:
                dbc_files.append((os.path.join(DBC_VOLUME, dbc_src['filepath']), dbc_src['can_bus_channel']))
            print(f'Loaded DBC file {dbc_src["filepath"]} with channel {dbc_src["can_bus_channel"]}')
    else:
        # Fallback to default DBC file in /dbc volume
        dbc_files.append((os.path.join('/dbc', '11-bit-OBD2-v4.0.dbc'), 0))

    database_files = {
            "CAN": dbc_files
    }

    decoded = mdf.extract_bus_logging(database_files)

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
    with open(CONFIG_PATH, 'r') as f:
        DATA['config'] = toml.load(f)


def get_config():
    return DATA.get('config')


def copy_defaults(config_path):
    config_ok = True
    dbc_ok = True

    if os.path.exists(config_path):
        print(f"Configuration file found at {config_path}")
    else:
        config_ok = copy_default(DEFAULT_DBC_PATH, config_path, 'config')

    target_dbc_path = os.path.join(DBC_VOLUME, os.path.basename(DEFAULT_DBC_PATH))

    if os.path.exists(target_dbc_path):
        print(f"DBC file found at {target_dbc_path}")
    else:
        dbc_ok = copy_default(DEFAULT_CONFIG_PATH, target_dbc_path, 'DBC')

    return config_ok and dbc_ok


def copy_default(src: str, dst: str, ftype: Literal['DBC', 'config']) -> bool:
    ok = True
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        with open(src, 'r') as src, open(dst, 'w') as dst:
            dst.write(src.read())

        print(f"Default {ftype} file copied to {dst}")
    else:
        print(f"Default {ftype} file not found at {src}")
        ok = False
    return ok

def download_dbcs():
    print("Downloading DBC files...")
    if get_config() is None:
        raise Exception("No config found!")

    config = get_config()
    dbc_src = config['dbc']['src'] if config and 'dbc' in config and 'src' in config['dbc'] else []

    for dbc in dbc_src:
        origin = dbc['origin'] if 'origin' in dbc else None
        if origin is None:
            print(f"No origin found for DBC file '{dbc['filepath']}', skipping download")
            continue

        r = requests.get(origin)
        r.raise_for_status()

        content = r.content

        if not os.path.exists(os.path.join(DBC_VOLUME, dbc['filepath'])):
            with open(os.path.join(DBC_VOLUME, dbc['filepath']), 'w') as f:
                f.write(content.decode('utf-8'))

            print(f"Downloaded DBC file to {dbc['filepath']}")
        else:
            print(f"DBC file already exists at {dbc['filepath']}, skipping download")



if __name__ == '__main__':
    if not copy_defaults(CONFIG_PATH):
        raise Exception("Could not copy defaults! Check your docker compose configuration!"
                        f"Currently:\n\tconfig={CONFIG_PATH},\n\tconfig_volume={CONFIG_VOLUME},\n\tdbc_volume={DBC_VOLUME}")

    fetch_config()
    download_dbcs()

    APP.run(host='0.0.0.0', port=5000, debug=True)
    APP.logger.info("Server started")

