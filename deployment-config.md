# HunyuanVideo-Avatar RunPod Serverless Configuration

## Endpoint Settings

### Basic Configuration
- **GPU Type**: A100 80GB (or RTX 4090 24GB minimum)
- **Worker Count**: 1
- **Container Disk**: 50GB
- **Network Volume**: None (using AWS S3 for storage)

### Timeout Settings
- **Request Timeout**: 1800s (30 minutes)
- **Worker Timeout**: 3600s (60 minutes)

## Environment Variables

### Required for AWS S3 Storage
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_DEFAULT_REGION=us-east-2
S3_BUCKET_NAME=my-runpod-storage-01
```

### Required for HunyuanVideo-Avatar
```
PYTHONPATH=/workspace
MODEL_BASE=/workspace/weights
```

## Deployment Steps

### 1. Create Endpoint
- Go to RunPod Console → Serverless → New Endpoint
- Select GitHub repository: `chandcalnaido/cchunyan`
- Set build context to root (`.`)
- Set Dockerfile path to `docker/Dockerfile`

### 2. Configure Environment Variables
Add all environment variables listed above in the endpoint creation dialog.

### 3. Configure GPU Resources
- Select GPU with 24GB+ VRAM (A100 recommended)
- Set worker count to 1
- Set container disk to 50GB

### 4. Advanced Settings
- Set request timeout to 1800s
- Set worker timeout to 3600s
- No network volume needed (using S3)

## AWS S3 Setup

### Bucket Configuration
- **Bucket Name**: my-runpod-storage-01
- **Region**: us-east-2
- **Type**: General Purpose
- **ACLs**: Disabled
- **Encryption**: SSE-S3 (default)

### IAM User Configuration
- **User Name**: runpod-backup
- **Access Type**: Programmatic access only
- **Policy**: AmazonS3FullAccess
- **Tags**: 
  - Name: runpod-backup
  - Purpose: S3 backup storage for RunPod HunyuanVideo project
  - Environment: production

## Testing

### Test Request
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

### Expected Response
```json
{
  "status": "success",
  "output_url": "/workspace/results/job_123/generated_video.mp4",
  "s3_url": "s3://my-runpod-storage-01/results/job_123/generated_video.mp4",
  "metadata": {
    "prompt": "A cat walking in the rain",
    "duration": 5,
    "fps": 24,
    "resolution": "704x704"
  }
}
```

## Cost Estimation

### AWS S3 Costs (us-east-2)
- **Storage**: ~$0.023/GB/month
- **API Calls**: ~$0.0004 per 1,000 requests
- **Data Transfer**: Free within region

### RunPod Costs
- **GPU**: Varies by GPU type
- **Container Storage**: Included in GPU cost
- **Network Volume**: $0 (not using)

## Troubleshooting

### Common Issues
1. **Model download fails**: Check AWS credentials and bucket permissions
2. **Video generation timeout**: Increase request timeout
3. **GPU out of memory**: Use GPU with more VRAM
4. **S3 upload fails**: Check bucket name and region

### Debug Commands
```bash
# Check S3 bucket access
aws s3 ls s3://my-runpod-storage-01 --region us-east-2

# Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $S3_BUCKET_NAME
```

## Future Enhancements

### S3-to-S3 Fallback (Optional)
To enable S3-to-S3 fallback, add these environment variables:
```
SECONDARY_S3_ACCESS_KEY_ID=AKIA...
SECONDARY_S3_SECRET_ACCESS_KEY=xxxxx
SECONDARY_S3_DATACENTER=us-east-1
SECONDARY_S3_NETWORK_VOLUME_ID=backup-bucket-name
```

Then uncomment the fallback code in `src/handler.py`. 