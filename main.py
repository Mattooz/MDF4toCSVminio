from fileinput import filename
from typing import Literal

from asammdf import MDF
import os
from flask import Flask, request
from minio import Minio
import re

app = Flask(__name__)
minio = Minio(endpoint=os.environ['MINIO_URL'], access_key=os.environ['MINIO_USER'], secret_key=os.environ['MINIO_PSW'],
              secure=False)

tmp_folder = os.path.join('.', 'tmp')

output_bucket = 'output'


@app.route(rule='/mdf-handle', methods=['POST'])
def handle():
    event = request.json

    try:
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            obj = record['s3']['object']['key']

            app.logger.info(f"Processing new file! Bucket: '{bucket}', File: '{obj}'.")

            mdf_in_path = get_mdf_path(obj, 'input')
            name = basename(obj)
            mdf_out_path = get_mdf_path(name, 'output', 'csv')

            minio.fget_object(bucket, obj, mdf_in_path)

            with open(mdf_in_path, 'rb+') as mdf_in_file, MDF(mdf_in_file) as mdf_in:
                handle_mdf(mdf_in, name)

            minio.fput_object(output_bucket, os.path.basename(mdf_out_path), mdf_out_path)

            app.logger.info(f"Done processing! Uploaded file '{basename}' to bucket '{output_bucket}'")
    except Exception as e:
        app.logger.error(f'Some went wrong: {e}')

    return '', 200


def handle_mdf(mdf: MDF, name: str):
    decoded = mdf.extract_bus_logging(
        database_files={
            "CAN": [(os.path.join('resources', '11-bit-OBD2-v4.0.dbc'), 0)]
        }
    )

    path = get_mdf_path(name, 'output')
    decoded.export(fmt='csv', filename=path, single_time_base=True, delimiter=',', quotechar='"', escapechar='\\')


def get_mdf_path(file_name: str, io: Literal['input', 'output'], extension: Literal['csv', 'mdf', None] = None):
    if io == 'input':
        return os.path.join(tmp_folder, 'mdf_in_' + file_name)
    elif io == 'output':
        if extension is not None:
            return os.path.join(tmp_folder, 'mdf_out_' + file_name + '.' + extension)
        else:
            return os.path.join(tmp_folder, 'mdf_out_' + file_name)
    else:
        raise Exception("Invalid IO id")

def basename(path):
    rgx = r'^(.+?)(?:\.[^.]+)?$'
    return re.match(rgx, path).group(1)

def setup():
    os.makedirs(tmp_folder, exist_ok=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
    app.logger.info("Server started")
