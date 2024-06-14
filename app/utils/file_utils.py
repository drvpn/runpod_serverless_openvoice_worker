'''
The MIT License (MIT)
Copyright © 2024 Dominic Powers

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''
import os
import requests
import shutil
import boto3
from botocore.config import Config

"""Downloads a file from a URL to a local path."""
def download_file(url, local_filename):
    try:
        print(f'[Enhancer]: Downloading {url}')
        if os.path.exists(local_filename):
            return local_filename, None
        with requests.get(url, stream=True) as r:
            r.raise_for_status()

            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return local_filename, None

    except Exception as e:
        return None, e

"""Uploads a file to an S3 bucket and makes it publicly readable."""
def upload_to_s3(local_file, bucket_name, object_name):
    try:
        print(f'[Enhancer]: Uploading {object_name}')
        s3_client = boto3.client('s3',
                                 endpoint_url=os.getenv('BUCKET_ENDPOINT_URL'),
                                 aws_access_key_id=os.getenv('BUCKET_ACCESS_KEY_ID'),
                                 aws_secret_access_key=os.getenv('BUCKET_SECRET_ACCESS_KEY'),
                                 config=Config(signature_version='s3v4'))
        s3_client.upload_file(local_file, bucket_name, object_name, ExtraArgs={'ACL': 'public-read'})

        return f"{os.getenv('BUCKET_ENDPOINT_URL')}/{bucket_name}/{object_name}", None
    except Exception as e:
        return None, e

def sync_checkpoints():

    try:
        # https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth
        # Ensure the models are downloaded and available
        model_paths = [
            ('/app/gfpgan/weights/GFPGANv1.4.pth', 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth'),
            ('/app/gfpgan/weights/detection_Resnet50_Final.pth', 'https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth'),
            ('/app/gfpgan/weights/parsing_parsenet.pth', 'https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth')
        ]

        for local_path, url in model_paths:
            if not os.path.exists(local_path):
                result, error = download_file(url, local_path)

                if error:
                    return None, error

        return None, None

    except Exception as e:
        return None, e

''' Link to network volume to OpenVoice checkpoints (if present)'''
def map_network_volume():

    try:
        # Detect network volume mount point
        if os.path.exists('/runpod-volume'):

            network_volume_path = '/runpod-volume'

        elif os.path.exists('/workspace'):

            network_volume_path = '/workspace'

        else:
            # No network volume
            network_volume_path = None

        # Identify network volume
        if network_volume_path is None:
            print(f'[Enhancer]: No network volume detected, using ephemeral storage')
        else:
            print(f'[Enhancer]: Network volume detected at {network_volume_path}')

        if network_volume_path is not None:
            # Ensure the enhancer cache directory exists on network volume
            os.makedirs(f'{network_volume_path}/gfpgan', exist_ok=True)

            # Remove existing .cache directory if it exists and create a symbolic link
            if os.path.islink('/app/gfpgan/weights') or os.path.exists('/app/gfpgan/weights'):
                if os.path.isdir('/app/gfpgan/weights'):
                    shutil.rmtree('/app/gfpgan/weights')

                else:
                    os.remove("/app/gfpgan/weights")

            # Create symlink to connect enhancer cache to network volume
            os.symlink(f'{network_volume_path}/gfpgan', '/app/gfpgan/weights')

        return None, None

    except Exception as e:
        return None, e
