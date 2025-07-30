# HunyuanVideo-Avatar RunPod Serverless

This repository contains a RunPod serverless implementation of the HunyuanVideo-Avatar model for video generation.

## Overview

This project provides a containerized version of Tencent's HunyuanVideo-Avatar model that can be deployed as a serverless endpoint on RunPod. The model generates videos based on text prompts.

## Architecture

- **Docker Container**: Based on RunPod's PyTorch image with CUDA support
- **Model**: HunyuanVideo-Avatar from Tencent
- **Deployment**: RunPod Serverless endpoint
- **API**: RESTful API for video generation requests

## Features

- Text-to-video generation using HunyuanVideo-Avatar
- Configurable video parameters (duration, FPS, resolution, seed, cfg_scale, infer_steps)
- Single GPU inference with FP8 optimization
- GPU-accelerated inference with CUDA support
- Health monitoring and real-time progress tracking
- Automatic model downloading to persistent storage
- Support for high-quality 704x704 resolution

## Usage

### Input Parameters

```json
{
  "prompt": "A cat walking in the rain",
  "duration": 5,
  "fps": 24,
  "resolution": "704x704",
  "seed": 128,
  "cfg_scale": 7.5,
  "infer_steps": 50
}
```

### Output

```json
{
  "status": "success",
  "output_url": "/workspace/results/job_123/generated_video.mp4",
  "metadata": {
    "prompt": "A cat walking in the rain",
    "duration": 5,
    "fps": 24,
    "resolution": "704x704",
    "seed": 128,
    "cfg_scale": 7.5,
    "infer_steps": 50,
    "frames": 120,
    "image_size": 704
  }
}
```

## Deployment

### Prerequisites
1. **Create a Network Volume** (required for model persistence):
   - Go to RunPod Console → Storage → New Network Volume
   - Select same datacenter as your endpoint
   - Name: `hunyuan-models` (or similar)
   - Size: 50GB (for 15-25GB models)
   - Create the network volume

### Deploy Endpoint

#### Option 1: Deploy from GitHub (Recommended)
1. **Connect GitHub to RunPod**:
   - Go to RunPod Settings → Connections → GitHub → Connect
   - Authorize RunPod to access your repository
2. **Deploy from GitHub**:
   - Go to Serverless → New Endpoint
   - Select "GitHub Repo" under Custom Source
   - Choose your repository and branch
   - Configure GPU resources (24GB+ VRAM recommended)
   - **Attach Network Volume** in Advanced section
   - Click "Create Endpoint"

#### Option 2: Deploy from Docker Hub
1. Build the Docker image using the GitHub Actions workflow
2. Deploy to RunPod serverless using the image: `chandcalnaido/hunyuan-runpod`
3. **Attach Network Volume**:
   - In endpoint configuration, expand "Advanced" section
   - Select your network volume from "Network Volume" dropdown
4. Configure the endpoint with appropriate GPU resources (24GB+ VRAM recommended)

### Important Notes
- **Build Time**: Model download happens during first worker start (not during build)
- **Network Volume**: Required to avoid 80GB image size limit
- **GPU Requirements**: Minimum 24GB VRAM (very slow), recommended 96GB VRAM

## Model Information

- **Base Model**: HunyuanVideo-Avatar
- **Model Size**: ~15-25GB (including models)
- **Network Volume**: Required for model persistence (50GB recommended)
- **Storage Cost**: ~$3.50/month for 50GB network volume
- **First Run Time**: ~10-60 minutes (model download on first worker start)
- **GPU Requirements**: 
  - **Minimum**: 24GB VRAM (very slow)
  - **Recommended**: 96GB VRAM for best quality
  - **CUDA**: 12.1+ required

## Development

### Local Testing

```bash
# Build the image locally
docker build -f docker/Dockerfile -t hunyuan-runpod .

# Run the container
docker run --gpus all -p 8000:8000 hunyuan-runpod
```

### Model Download Verification

The model download process uses the official HunyuanVideo-Avatar repository. If you encounter issues with model downloads, please refer to the [official HunyuanVideo-Avatar documentation](https://github.com/Tencent-Hunyuan/HunyuanVideo-Avatar) for the latest download instructions.

### Testing the Handler

```python
import requests

# Test the endpoint
response = requests.post("http://localhost:8000/run", json={
    "input": {
        "prompt": "A beautiful sunset",
        "duration": 3,
        "fps": 24,
        "resolution": "512x512"
    }
})

print(response.json())
```

## Requirements

- Python 3.10+
- PyTorch 2.1.0+
- CUDA 12.1+
- 16GB+ VRAM recommended
- 50GB+ storage for models

## License

This project uses the HunyuanVideo-Avatar model from Tencent. Please refer to their licensing terms.
