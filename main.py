from os import access

from asammdf import MDF
import os
from flask import Flask, request
from minio import Minio

app = Flask(__name__)
minio = Minio(endpoint='minio:9000', access_key=os.environ['MINIO_USER'], secret_key=os.environ['MINIO_PSW'],
              secure=False)

mdf_in_path = os.path.join('.', 'mdf_in.mf4')
mdf_out_path = os.path.join('.', 'mdf_out')

output_bucket = 'output'


@app.route(rule='/mdf-handle', methods=['POST'])
def handle():
    event = request.json

    print("PUT EVENT")
    try:
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            obj = record['s3']['object']['key']

            print(f"Processing new file! Bucket: '{bucket}', File: '{obj}'.")

            minio.fget_object(bucket, obj, mdf_in_path)

            with open(mdf_in_path, 'rb+') as mdf_in_file, MDF(mdf_in_file) as mdf_in:
                handle_mdf(mdf_in)

            basename = os.path.basename(obj) + ".csv"

            minio.fput_object(output_bucket, basename, mdf_out_path + ".csv")

            print(f"Done processing! Uploaded file '{basename}' to bucket '{output_bucket}'")
    except Exception as e:
        print('Some went wrong: ', e)

    return '', 200


def handle_mdf(mdf: MDF):
    decoded = mdf.extract_bus_logging(
        database_files={
            "CAN": [(os.path.join('resources', '11-bit-OBD2-v4.0.dbc'), 0)]
        }
    )

    decoded.export(fmt='csv', filename=mdf_out_path, single_time_base=True, delimiter=',', quotechar='"', escapechar='\\')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
