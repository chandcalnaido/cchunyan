# S3 Storage Component for RunPod Projects

This component provides S3-compatible storage functionality for RunPod network volumes, making it easy to manage models, datasets, and generated files across multiple RunPod projects.

## Features

- ✅ **Model Persistence**: Download and store large models in S3
- ✅ **File Management**: Upload/download files with progress tracking
- ✅ **Multi-Project Support**: Share models across different RunPod projects
- ✅ **Fallback Support**: Graceful degradation to network volumes
- ✅ **Easy Integration**: Simple API for any RunPod project
- ✅ **Cost Effective**: S3 storage is cheaper than network volumes

## Quick Start

### 1. Setup RunPod S3 API

1. **Create Network Volume**:
   - Go to RunPod Console → Storage → New Network Volume
   - Choose a supported datacenter (US-KS-2, EUR-IS-1, etc.)
   - Set size to 50GB+ for models

2. **Create S3 API Key**:
   - Go to RunPod Settings → S3 API Keys → Create S3 API Key
   - Save the access key and secret

3. **Get Network Volume ID**:
   - Note the network volume ID from the Storage page

### 2. Configure Environment Variables

Set these environment variables in your RunPod endpoint:

```bash
RUNPOD_S3_ACCESS_KEY_ID=user_xxx...
RUNPOD_S3_SECRET_ACCESS_KEY=rps_xxx...
RUNPOD_DATACENTER=US-KS-2
RUNPOD_NETWORK_VOLUME_ID=your_volume_id
```

### 3. Use in Your Project

```python
from s3_storage import RunPodS3Storage

# Initialize S3 storage
s3_storage = RunPodS3Storage(
    access_key_id="user_xxx...",
    secret_access_key="rps_xxx...",
    datacenter="US-KS-2",
    network_volume_id="your_volume_id"
)

# Download models
s3_storage.download_models("tencent/HunyuanVideo-Avatar")

# Upload results
s3_storage.upload_file("local_video.mp4", "results/video.mp4")
```

## API Reference

### RunPodS3Storage Class

#### Initialization

```python
s3_storage = RunPodS3Storage(
    access_key_id="user_xxx...",
    secret_access_key="rps_xxx...",
    datacenter="US-KS-2",
    network_volume_id="your_volume_id",
    timeout=7200  # Optional: 2 hours default
)
```

#### Methods

##### Model Management

```python
# Download models from HuggingFace to S3
success = s3_storage.download_models("tencent/HunyuanVideo-Avatar")

# Check if model exists in S3
exists = s3_storage.file_exists("weights/ckpts/model.pt")

# Download model from S3 to local
success = s3_storage.download_file("weights/ckpts/model.pt", "/local/path/model.pt")
```

##### File Operations

```python
# Upload single file
success = s3_storage.upload_file("local_file.mp4", "results/video.mp4")

# Download single file
success = s3_storage.download_file("results/video.mp4", "local_file.mp4")

# List files
files = s3_storage.list_files("results/")

# Delete file
success = s3_storage.delete_file("results/old_video.mp4")

# Check file exists
exists = s3_storage.file_exists("results/video.mp4")
```

##### Storage Information

```python
# Get storage statistics
info = s3_storage.get_storage_info()
print(f"Total files: {info['total_files']}")
print(f"Total size: {info['total_size_gb']} GB")

# Get S3 URL for file
url = s3_storage.get_file_url("results/video.mp4")
```

### Environment Variables Helper

```python
from s3_storage import create_s3_storage_from_env

# Create from environment variables
s3_storage = create_s3_storage_from_env()
```

## Integration Examples

### 1. Model Loading with S3

```python
def load_model():
    try:
        # Try S3 first
        s3_storage = create_s3_storage_from_env()
        if s3_storage.file_exists("weights/model.pt"):
            s3_storage.download_file("weights/model.pt", "/local/model.pt")
            return load_local_model("/local/model.pt")
    except:
        # Fallback to network volume
        pass
    
    # Network volume fallback
    if Path("/runpod-volume/weights/model.pt").exists():
        return load_local_model("/runpod-volume/weights/model.pt")
    
    # Download and store in S3
    download_models()
    return load_local_model("/local/model.pt")
```

### 2. Result Upload

```python
def generate_and_upload(job):
    # Generate result
    result_file = generate_video(job)
    
    # Upload to S3
    s3_storage = create_s3_storage_from_env()
    s3_key = f"results/job_{job['id']}/{result_file.name}"
    
    if s3_storage.upload_file(str(result_file), s3_key):
        return {
            "status": "success",
            "local_url": str(result_file),
            "s3_url": s3_storage.get_file_url(s3_key)
        }
    else:
        return {"status": "error", "message": "Upload failed"}
```

### 3. Multi-Project Model Sharing

```python
# Project A: Upload models
s3_storage = RunPodS3Storage(...)
s3_storage.download_models("tencent/HunyuanVideo-Avatar")

# Project B: Use same models
s3_storage = RunPodS3Storage(...)  # Same network volume
if s3_storage.file_exists("weights/ckpts/model.pt"):
    s3_storage.download_file("weights/ckpts/model.pt", "/local/model.pt")
```

## Supported Datacenters

| Datacenter | Endpoint URL                        |
| ---------- | ----------------------------------- |
| `EUR-IS-1` | `https://s3api-eur-is-1.runpod.io/` |
| `EU-RO-1`  | `https://s3api-eu-ro-1.runpod.io/`  |
| `EU-CZ-1`  | `https://s3api-eu-cz-1.runpod.io/`  |
| `US-KS-2`  | `https://s3api-us-ks-2.runpod.io/`  |

## Cost Comparison

### Network Volume Storage
- $0.07/GB/month (first 1TB)
- $0.05/GB/month (additional)

### S3 Storage Benefits
- ✅ **Shared across projects**: One volume for multiple endpoints
- ✅ **No duplication**: Models stored once, used everywhere
- ✅ **Cost effective**: Pay once, use everywhere
- ✅ **Scalable**: Easy to add more projects

## Error Handling

The component includes comprehensive error handling:

```python
try:
    s3_storage = create_s3_storage_from_env()
    # Use S3 storage
except ValueError as e:
    print(f"S3 configuration error: {e}")
    # Fallback to network volume
except Exception as e:
    print(f"S3 error: {e}")
    # Fallback to network volume
```

## Best Practices

### 1. Model Organization
```
s3://your-volume/
├── weights/
│   ├── hunyuan-video-avatar/
│   ├── stable-diffusion/
│   └── other-models/
├── results/
│   ├── project-a/
│   └── project-b/
└── datasets/
    └── training-data/
```

### 2. Environment Variables
```bash
# Required
RUNPOD_S3_ACCESS_KEY_ID=user_xxx...
RUNPOD_S3_SECRET_ACCESS_KEY=rps_xxx...
RUNPOD_DATACENTER=US-KS-2
RUNPOD_NETWORK_VOLUME_ID=your_volume_id

# Optional
AWS_MAX_ATTEMPTS=10  # For large files
AWS_RETRY_MODE=standard
```

### 3. File Naming
- Use descriptive paths: `results/job_123/video_2024-01-15.mp4`
- Include job IDs for tracking
- Use consistent naming conventions

## Troubleshooting

### Common Issues

1. **"Invalid S3 credentials"**
   - Check your S3 API key and secret
   - Verify they're correctly set in environment variables

2. **"Network volume not found"**
   - Verify the network volume ID
   - Check that the volume is in the correct datacenter

3. **"Access denied"**
   - Verify S3 API key permissions
   - Check that the network volume is accessible

4. **"Timeout errors"**
   - Increase timeout for large files
   - Set `AWS_MAX_ATTEMPTS=10`

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

s3_storage = RunPodS3Storage(...)
# Will show detailed S3 operations
```

## Migration from Network Volumes

If you're migrating from network volumes to S3:

1. **Export existing data**:
   ```bash
   # Copy from network volume to S3
   aws s3 sync /runpod-volume/ s3://your-volume/ --endpoint-url https://s3api-us-ks-2.runpod.io/
   ```

2. **Update your code**:
   ```python
   # Old: Direct file access
   model_path = "/runpod-volume/weights/model.pt"
   
   # New: S3 with fallback
   s3_storage = create_s3_storage_from_env()
   if s3_storage.file_exists("weights/model.pt"):
       s3_storage.download_file("weights/model.pt", "/local/model.pt")
       model_path = "/local/model.pt"
   ```

3. **Test thoroughly**:
   - Verify all files are accessible
   - Test upload/download operations
   - Monitor costs and performance

## Contributing

This component is designed to be easily reusable across RunPod projects. To contribute:

1. **Add new features**: Extend the `RunPodS3Storage` class
2. **Improve error handling**: Add more specific error types
3. **Add new datacenters**: Update the `S3_ENDPOINTS` dictionary
4. **Create examples**: Add more integration examples

## License

This component is part of the HunyuanVideo-Avatar RunPod project and follows the same licensing terms. 