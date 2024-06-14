<<<<<<< HEAD
import runpod
import urllib.request
import zipfile
import requests
import warnings
import boto3
from botocore.config import Config
import random
import string
import hashlib
import datetime
import sys
import os
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS
=======
'''
The MIT License (MIT)
Copyright © 2024 Dominic Powers

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import warnings
>>>>>>> eb22df3 (Initial commit)

''' Suppress all warnings (FOR PRODUCTION) '''
warnings.filterwarnings("ignore")

<<<<<<< HEAD
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

        if network_volume_path is not None:
            # Ensure the whisper cache directory exists on network volume
            os.makedirs(f'{network_volume_path}/OpenVoice', exist_ok=True)

            # Remove existing .cache directory if it exists and create a symbolic link
            if os.path.islink('/app/checkpoints_v2') or os.path.exists('/app/checkpoints_v2'):
                if os.path.isdir('/app/checkpoints_v2'):
                    shutil.rmtree('/app/checkpoints_v2')

                else:
                    os.remove("/app/checkpoints_v2")

            # Create symlink to connect whisper cache to network volume
            os.symlink(f'{network_volume_path}/OpenVoice', '/app/checkpoints_v2')
        return None, None
    except Exception as e:
        return None, e


''' Check if all required directories exist.'''
def check_directories(base_dir, dirs):
    try:
        for dir in dirs:
            if not os.path.exists(os.path.join(base_dir, dir)):
                return False, None
        return True, None
    except Exception as e:
        return None, e

''' Download the zip file and unzip it into the target directory.'''
def download_and_unzip(url, target_dir, zip_filename):

    try:
        # Download the zip file
        urllib.request.urlretrieve(url, zip_filename)

        # Unzip the file
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

        # Remove the zip file
        os.remove(zip_filename)

        return None, None

    except Exception as e:
        return None, e

''' Generate a unique timestamped filename '''
def generate_unique_filename(base_title='outputs_v2/OpenVoice', extension='.wav'):
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        hash_str = hashlib.md5(base_title.encode()).hexdigest()[:6]

        filename = f'{base_title}_{timestamp}_{random_str}_{hash_str}{extension}'

        return filename, None

    except Exception as e:
        return None, e

''' Downloads a file from a URL to a local path. '''
def download_file(url, local_filename):
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return local_filename, None
    except Exception as e:
        return None, e

''' Uploads a file to an S3 bucket and makes it publicly readable.
    ENV variables BUCKET_ENDPOINT_URL, BUCKET_ACCESS_KEY_ID, and BUCKET_SECRET_ACCESS_KEY are required '''
def upload_to_s3(local_file, bucket_name, object_name):
    try:
        s3_client = boto3.client('s3',
                                 endpoint_url=os.getenv('BUCKET_ENDPOINT_URL'),
                                 aws_access_key_id=os.getenv('BUCKET_ACCESS_KEY_ID'),
                                 aws_secret_access_key=os.getenv('BUCKET_SECRET_ACCESS_KEY'),
                                 config=Config(signature_version='s3v4'))

        s3_client.upload_file(local_file, bucket_name, object_name, ExtraArgs={'ACL': 'public-read'})

        return f"{os.getenv('BUCKET_ENDPOINT_URL')}/{bucket_name}/{object_name}", None

    except Exception as e:
        return None, e

''' Main function to check directories and download/unzip if necessary.'''
def sync_checkpoints(url, target_dir, zip_filename, required_dirs):

    # Check if the required directories exist
    result, error = check_directories(target_dir, required_dirs)

    if error:
        return None, error

    if result:
        print('[OpenVoice]: Cached models present')
        return None, None

    else:
        print('[OpenVoice]: Loading models into Cache')

        result, error = download_and_unzip(url, target_dir, zip_filename)

        if error:
            return None, error
        else:
            return None, None

''' Call openview model to convert text to speech
    ENV variable BUCKET_NAME can set your bucket name, which defaults to OpenVoive'''
def generate_wav(language, text, reference_speaker='resources/example_reference.mp3', speed=1.0):

    try:
        # Prepare defaults
        bucket_name = os.getenv('BUCKET_NAME', 'OpenVoice')
        ckpt_converter = 'checkpoints_v2/converter'

        output_dir = 'outputs_v2'
        os.makedirs('outputs_v2', exist_ok=True)

        src_path = f'{output_dir}/tmp.wav'

        # Detect and output device type
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        print(f'[OpenVoice]: [device]: {device}')

        # Obtain Tone Color Embedding
        tone_color_converter = ToneColorConverter(f'{ckpt_converter}/config.json', device=device)
        tone_color_converter.load_ckpt(f'{ckpt_converter}/checkpoint.pth')

        target_se, audio_name = se_extractor.get_se(reference_speaker, tone_color_converter, vad=False)

        # Initialize TTS model
        model = TTS(language=language, device=device)
        speaker_ids = model.hps.data.spk2id

        for speaker_key in speaker_ids.keys():
            speaker_id = speaker_ids[speaker_key]
            speaker_key = speaker_key.lower().replace('_', '-')

            source_se = torch.load(f'checkpoints_v2/base_speakers/ses/{speaker_key}.pth', map_location=device)
            model.tts_to_file(text, speaker_id, src_path, speed=speed)
            output_audio_path, error = generate_unique_filename()
            if error:
                return None, error

            # Run the tone color converter
            encode_message = '@MyShell'
            tone_color_converter.convert(
                audio_src_path=src_path,
                src_se=source_se,
                tgt_se=target_se,
                output_path=output_audio_path,
                message=encode_message)

        # Upload audio to S3 bucket
        object_name = os.path.basename(output_audio_path)

        uploaded_url, error = upload_to_s3(output_audio_path, bucket_name, object_name)
        if error:
            return None, error
=======
import runpod
import os
import cv2
import numpy as np
import torch
import time
import multiprocessing
from gfpgan import GFPGANer

from utils.file_utils import download_file, upload_to_s3, sync_checkpoints, map_network_volume

def enhance_faces_in_video(input_video_url, bucket_name):
    try:
        print(f'[Enhancer]: Processing GFPGAN enhancer on {input_video_url}')
        # Download the input video
        input_video_path, error = download_file(input_video_url, 'input_video.mp4')

        if error:
            return None, error

        # Generate the output video path
        timestamp = time.strftime("%Y_%m_%d_%H.%M.%S")
        output_video_path = f"enhanced_{timestamp}.mp4"

        # Initialize GFPGAN with the correct model path
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f'[Enhancer]: [device]: {device}')

        # call model
        gfpganer = GFPGANer(model_path='/app/gfpgan/weights/GFPGANv1.4.pth', upscale=2, arch='clean', channel_multiplier=2, device=device)

        # Read the input video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise FileNotFoundError("Error: Could not open input video.")

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Temporary directory for frames
        tmp_dir = 'temp_frames'
        os.makedirs(tmp_dir, exist_ok=True)

        frame_number = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            # Ensure frame dimensions are correct
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))

            # Enhance the face in the frame using GFPGAN
            _, _, enhanced_frame = gfpganer.enhance(frame, has_aligned=False, only_center_face=False, paste_back=True)

            # Save enhanced frame to disk
            frame_path = os.path.join(tmp_dir, f"frame_{frame_number:06d}.png")
            cv2.imwrite(frame_path, enhanced_frame)
            frame_number += 1

        cap.release()

        # Get the number of CPU cores
        num_cores = multiprocessing.cpu_count()

        # Use ffmpeg to combine frames into a video and include audio
        cmd = (
            f"ffmpeg -y -loglevel error -thread_queue_size {num_cores} -r {fps} -i {tmp_dir}/frame_%06d.png "
            f"-i {input_video_path} -c:v libx264 -pix_fmt yuv420p -profile:v baseline -level 3.0 "
            f"-c:a aac -strict experimental -b:a 128k -movflags +faststart {output_video_path}"
        )
        os.system(cmd)

        # Clean up temporary frames
        for file_name in os.listdir(tmp_dir):
            file_path = os.path.join(tmp_dir, file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        os.rmdir(tmp_dir)

        # Upload the enhanced video to S3
        object_name = os.path.basename(output_video_path)

        uploaded_url, error = upload_to_s3(output_video_path, bucket_name, object_name)
        if error:
            print(f'[Enhancer][ERROR]: upload_to_s3 failed {error}')
            sys.exit(1)

        # Try to clean up local files
        try:
            os.remove(input_video_path)
            os.remove(output_video_path)
        except:
            pass
>>>>>>> eb22df3 (Initial commit)

        return uploaded_url, None

    except Exception as e:
        return None, e

<<<<<<< HEAD
''' RunPod Handler function that will be used to process jobs. '''
def handler(job):
    job_input = job['input']

    # Print startup header
    print(f'[OpenVoice]: Processing job request')

    # text option - Text to convert to speech
    """
    OPTION: text 
    DEFAULT VALUE: None (REQUIRED) 
    AVAILABLE OPTIONS: Any text you want to convert to speech
    *Override default value using ENV variable DEFAULT_TEXT 
    """
    text = job_input.get('text', os.getenv('DEFAULT_TEXT', None))

    # language option - Language text is written in
    """
    OPTION: language 
    DEFAULT VALUE: EN_NEWEST 
    AVAILABLE OPTIONS: One of ['EN', 'EN-AU', 'EN-BR', 'EN-INDIA', 'EN-US', 'EN-DEFAULT', 'EN-NEWEST', 'ES', 'FR', 'ZH', 'JP', 'KR']
    *Override default value using ENV variable DEFAULT_LANGUAGE 
    """
    language = job_input.get('language', os.getenv('DEFAULT_LANGUAGE', 'EN_NEWEST'))

    # voice_url - URL to an mp3 file with the desired speaker's voice recorded
    """
    OPTION: voice_url 
    DEFAULT VALUE: None (REQUIRED) 
    AVAILABLE OPTIONS: Any valid URL to a short mp3 file with a clear recording of the desired voice
    *Override default value using ENV variable DEFAULT_VOICE_URL 
    """
    voice_url = job_input.get('voice_url', os.getenv('DEFAULT_VOICE_URL', None))

    # speed option - Speed at which to speak text
    """
    OPTION: speed 
    DEFAULT VALUE: 1.0 
    AVAILABLE OPTIONS: Look up the range and place here
    *Override default value using ENV variable DEFAULT_SPEED 
    """
    speed = job_input.get('speed', os.getenv('DEFAULT_SPEED', 1.0))

    reference_speaker, error = download_file(voice_url, 'tmp/video.mp4')
    if error:
        print(f'ERROR in download_file: {error}')
        sys.exit(1)
    else:
        output_audio_url, error = generate_wav(language=language, text=text, reference_speaker=reference_speaker, speed=speed)
        if error:
            print(f'ERROR in generate_wav: {error}')
            sys.exit(1)
        else:
            return {
                'output_audio_url': output_audio_url
            }

if __name__ == '__main__':

    # Stored model
    url = 'https://myshell-public-repo-hosting.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip'
    target_dir = '/app'
    zip_filename = os.path.join(target_dir, 'checkpoints_v2_0417.zip')

    # Define the required directory structure for model
    required_dirs = [
        'checkpoints_v2',
        'checkpoints_v2/base_speakers',
        'checkpoints_v2/base_speakers/ses',
        'checkpoints_v2/converter'
    ]

    # Map network volume if attached
    result, error = map_network_volume()
    if error:
        print(f'[OpenVoice][WARNING]: map_network_volume failed: {error}')

    # Initial load (if needed) to populate network volume with checkpoints
    result, error = sync_checkpoints(url, target_dir, zip_filename, required_dirs)
    if error:
        print(f'[OpenVoice][ERROR]: Failed to download checkpoints: {error}')
        sys.exit(1)

    runpod.serverless.start({'handler': handler})
=======
""" Handler function that will be used to process jobs. """
def handler(job):
    job_input = job['input']

    input_video_url = job_input.get('input_video_url')
    bucket_name = 'Enhanced_GFPGAN'

    if not input_video_url:
        return {"error": "'input_video_url' is required in job input."}

    result, error = enhance_faces_in_video(input_video_url, bucket_name)

    if error:
        print(f'[Enhancer][ERROR]: enahnce_faces_in_video failed: {error}')
        sys.exit(1)
    else:
        return {"output_video_url": result}

if __name__ == "__main__":

    result, error = map_network_volume()
    if error:
        print(f'[Enhancer][WARNING]: Could not map network volume: {error}')

    # Initial load (if needed) to populate network volume with checkpoints
    result, error = sync_checkpoints()
    
    if error:
        print(f'[Enhancer][ERROR]: Failed to download checkpoints: {error}')
        sys.exit(1)

    runpod.serverless.start({"handler": handler})
>>>>>>> eb22df3 (Initial commit)
