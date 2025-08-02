# docker/Dockerfile
# Use stable PyTorch base image that exists, then upgrade to 2.4.0
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-devel

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install runpod huggingface_hub[cli] ninja

# Upgrade to PyTorch 2.4.0 (matching HunyuanVideo-Avatar requirements)
RUN pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121

# Clone HunyuanVideo-Avatar
RUN git clone https://github.com/Tencent-Hunyuan/HunyuanVideo-Avatar.git .

# Install project requirements (use the official requirements.txt from HunyuanVideo-Avatar)
RUN pip install -r requirements.txt

# Install Flash Attention
RUN pip install git+https://github.com/Dao-AILab/flash-attention.git@v2.6.3

# Create directories for local storage (network volume will be mounted at /runpod-volume)
RUN mkdir -p /workspace/results /workspace/temp

# Return to workspace directory
WORKDIR /workspace

# Copy our RunPod handler
COPY ./src/handler.py /workspace/handler.py

# Set environment variables
ENV PYTHONPATH=/workspace
ENV MODEL_BASE=/workspace/weights

# Download models (uncomment and customize based on HunyuanVideo requirements)
# RUN python -c "
# import huggingface_hub
# # Download main model
# huggingface_hub.snapshot_download(
#     repo_id='hunyuanvideo/HunyuanVideo', 
#     local_dir='/workspace/weights/hunyuanvideo',
#     token=None  # Add token if needed
# )
# # Download other required models
# # Add other model downloads as needed
# "

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=300s --retries=3 \
    CMD python -c "import runpod; print('healthy')" || exit 1

# Start the handler
CMD ["python", "handler.py"]