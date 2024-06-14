<<<<<<< HEAD
FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04

# Set environment variable to avoid timezone configuration prompt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.9, pip, ffmpeg, and git
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.9 \
    python3.9-distutils \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configure the timezone (set to UTC)
RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata
=======
FROM python:3.11-slim
>>>>>>> eb22df3 (Initial commit)

# Set the working directory to /app
WORKDIR /app

<<<<<<< HEAD
# Add app files (Worker Template)
COPY app /app

# Update alternatives to use Python 3.9
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

# Set LD_LIBRARY_PATH environment variable
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/python3.9/dist-packages/nvidia/cudnn/lib

# Install required pip modules
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install tensorboard==2.13.0 && \
    python3 -m pip install git+https://github.com/myshell-ai/MeloTTS.git && \
    python3 -m pip install --upgrade -r /app/requirements.txt --no-cache-dir && \
    python3 -m unidic download && \
    rm /app/requirements.txt

# Set the default command to run the handler
CMD ["python3", "-u", "/app/handler.py"]
=======
# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Add app files (Worker Template)
COPY app /app

# Install torch and torchvision with the specific versions
RUN python3.11 -m pip install --upgrade pip && \
    python3.11 -m pip install torch==2.0.0+cu117 torchvision==0.15.0+cu117 --extra-index-url https://download.pytorch.org/whl/cu117 && \
    python3.11 -m pip install --upgrade -r /app/requirements.txt --no-cache-dir && \
    rm /app/requirements.txt

# Create symbolic links to the network volume
RUN ln -s runpod-volume/gfpgan/weights /app/gfpgan/weights

CMD ["python3.11", "-u", "/app/handler.py"]
>>>>>>> eb22df3 (Initial commit)
