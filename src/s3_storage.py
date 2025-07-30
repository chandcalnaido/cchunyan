# src/s3_storage.py
"""
Reusable S3 Storage Component for RunPod Projects

This module provides S3-compatible storage functionality for RunPod network volumes.
It can be easily integrated into other RunPod projects for model persistence and file management.

Usage:
    from s3_storage import RunPodS3Storage
    
    # Initialize with your RunPod S3 credentials
    s3_storage = RunPodS3Storage(
        access_key_id="user_xxx...",
        secret_access_key="rps_xxx...",
        datacenter="US-KS-2",
        network_volume_id="your_volume_id"
    )
    
    # Download models to S3
    s3_storage.download_models("tencent/HunyuanVideo-Avatar")
    
    # Upload generated files
    s3_storage.upload_file("local_file.mp4", "results/video.mp4")
"""

import os
import boto3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RunPodS3Storage:
    """
    S3-compatible storage wrapper for RunPod network volumes.
    
    This class provides a simple interface for managing files on RunPod network volumes
    using the S3-compatible API. It handles authentication, file transfers, and
    common operations like model downloads and result uploads.
    """
    
    # RunPod S3 endpoint URLs by datacenter
    S3_ENDPOINTS = {
        "EUR-IS-1": "https://s3api-eur-is-1.runpod.io/",
        "EU-RO-1": "https://s3api-eu-ro-1.runpod.io/",
        "EU-CZ-1": "https://s3api-eu-cz-1.runpod.io/",
        "US-KS-2": "https://s3api-us-ks-2.runpod.io/",
    }
    
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        datacenter: str,
        network_volume_id: str,
        timeout: int = 7200
    ):
        """
        Initialize the S3 storage client.
        
        Args:
            access_key_id: RunPod S3 API access key (e.g., user_xxx...)
            secret_access_key: RunPod S3 API secret key (e.g., rps_xxx...)
            datacenter: RunPod datacenter ID (e.g., "US-KS-2")
            network_volume_id: Network volume ID to use as S3 bucket
            timeout: Request timeout in seconds (default: 2 hours for large files)
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.datacenter = datacenter.upper()
        self.network_volume_id = network_volume_id
        self.timeout = timeout
        
        # Validate datacenter
        if self.datacenter not in self.S3_ENDPOINTS:
            raise ValueError(f"Unsupported datacenter: {datacenter}. Supported: {list(self.S3_ENDPOINTS.keys())}")
        
        # Get endpoint URL
        self.endpoint_url = self.S3_ENDPOINTS[self.datacenter]
        
        # Initialize S3 client
        self.s3_client = self._create_s3_client()
        
        logger.info(f"Initialized S3 storage for datacenter: {self.datacenter}")
        logger.info(f"Network volume: {self.network_volume_id}")
        logger.info(f"Endpoint: {self.endpoint_url}")
    
    def _create_s3_client(self) -> boto3.client:
        """Create and configure the S3 client."""
        try:
            config = Config(
                read_timeout=self.timeout,
                retries={'max_attempts': 10, 'mode': 'standard'}
            )
            
            client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.datacenter,
                endpoint_url=self.endpoint_url,
                config=config
            )
            
            # Test connection
            client.head_bucket(Bucket=self.network_volume_id)
            logger.info("✅ S3 client initialized successfully")
            return client
            
        except NoCredentialsError:
            raise ValueError("Invalid S3 credentials. Please check your access_key_id and secret_access_key.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise ValueError(f"Network volume '{self.network_volume_id}' not found or not accessible.")
            elif error_code == '403':
                raise ValueError("Access denied. Please check your S3 API credentials and permissions.")
            else:
                raise Exception(f"S3 client initialization failed: {e}")
    
    def download_models(self, model_id: str, local_dir: str = "/workspace/weights") -> bool:
        """
        Download models from HuggingFace to S3 storage.
        
        Args:
            model_id: HuggingFace model ID (e.g., "tencent/HunyuanVideo-Avatar")
            local_dir: Local directory to download models to first
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"🔄 Starting model download: {model_id}")
            logger.info(f"📁 Local directory: {local_dir}")
            logger.info(f"☁️  S3 destination: s3://{self.network_volume_id}/weights/")
            
            # Create local directory
            Path(local_dir).mkdir(parents=True, exist_ok=True)
            
            # Download models using huggingface-cli
            import subprocess
            import sys
            
            cmd = [
                "huggingface-cli", "download",
                model_id,
                "--local-dir", local_dir
            ]
            
            logger.info(f"📥 Running: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Stream output
            for line in process.stdout:
                logger.info(f"📥 {line.strip()}")
                sys.stdout.flush()
            
            process.wait()
            
            if process.returncode != 0:
                logger.error("❌ Model download failed")
                return False
            
            logger.info("✅ Model download completed")
            
            # Upload to S3
            logger.info("☁️  Uploading models to S3...")
            self._upload_directory(local_dir, "weights/")
            
            logger.info("✅ Models successfully uploaded to S3")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model download failed: {e}")
            return False
    
    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a single file to S3.
        
        Args:
            local_path: Local file path
            s3_key: S3 object key (destination path)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(local_path):
                logger.error(f"❌ Local file not found: {local_path}")
                return False
            
            logger.info(f"📤 Uploading: {local_path} -> s3://{self.network_volume_id}/{s3_key}")
            
            self.s3_client.upload_file(local_path, self.network_volume_id, s3_key)
            
            logger.info(f"✅ Upload successful: s3://{self.network_volume_id}/{s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a single file from S3.
        
        Args:
            s3_key: S3 object key (source path)
            local_path: Local file path (destination)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"📥 Downloading: s3://{self.network_volume_id}/{s3_key} -> {local_path}")
            
            # Create directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(self.network_volume_id, s3_key, local_path)
            
            logger.info(f"✅ Download successful: {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in S3 with optional prefix.
        
        Args:
            prefix: S3 key prefix to filter by
            
        Returns:
            List of file keys
        """
        try:
            logger.info(f"📋 Listing files with prefix: {prefix}")
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.network_volume_id,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
            
            logger.info(f"✅ Found {len(files)} files")
            return files
            
        except Exception as e:
            logger.error(f"❌ List files failed: {e}")
            return []
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.network_volume_id, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"❌ Error checking file existence: {e}")
                return False
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"🗑️  Deleting: s3://{self.network_volume_id}/{s3_key}")
            
            self.s3_client.delete_object(Bucket=self.network_volume_id, Key=s3_key)
            
            logger.info(f"✅ Delete successful: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Delete failed: {e}")
            return False
    
    def _upload_directory(self, local_dir: str, s3_prefix: str) -> bool:
        """
        Upload an entire directory to S3.
        
        Args:
            local_dir: Local directory path
            s3_prefix: S3 key prefix for uploaded files
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            local_path = Path(local_dir)
            if not local_path.exists():
                logger.error(f"❌ Local directory not found: {local_dir}")
                return False
            
            uploaded_count = 0
            failed_count = 0
            
            for file_path in local_path.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for S3 key
                    relative_path = file_path.relative_to(local_path)
                    s3_key = f"{s3_prefix}{relative_path}"
                    
                    if self.upload_file(str(file_path), s3_key):
                        uploaded_count += 1
                    else:
                        failed_count += 1
            
            logger.info(f"📤 Directory upload complete: {uploaded_count} successful, {failed_count} failed")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"❌ Directory upload failed: {e}")
            return False
    
    def get_file_url(self, s3_key: str) -> str:
        """
        Get the S3 URL for a file (for reference only, not for direct access).
        
        Args:
            s3_key: S3 object key
            
        Returns:
            str: S3 URL
        """
        return f"s3://{self.network_volume_id}/{s3_key}"
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage information and statistics.
        
        Returns:
            Dict with storage information
        """
        try:
            files = self.list_files()
            total_files = len(files)
            
            # Calculate total size (approximate)
            total_size = 0
            for file_key in files:
                try:
                    response = self.s3_client.head_object(Bucket=self.network_volume_id, Key=file_key)
                    total_size += response.get('ContentLength', 0)
                except:
                    pass
            
            return {
                "datacenter": self.datacenter,
                "network_volume_id": self.network_volume_id,
                "endpoint_url": self.endpoint_url,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_gb": round(total_size / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get storage info: {e}")
            return {}


# Convenience function for easy integration
def create_s3_storage_from_env() -> RunPodS3Storage:
    """
    Create S3 storage instance from environment variables.
    
    Required environment variables:
    - RUNPOD_S3_ACCESS_KEY_ID
    - RUNPOD_S3_SECRET_ACCESS_KEY
    - RUNPOD_DATACENTER
    - RUNPOD_NETWORK_VOLUME_ID
    
    Returns:
        RunPodS3Storage instance
    """
    access_key_id = os.environ.get("RUNPOD_S3_ACCESS_KEY_ID")
    secret_access_key = os.environ.get("RUNPOD_S3_SECRET_ACCESS_KEY")
    datacenter = os.environ.get("RUNPOD_DATACENTER")
    network_volume_id = os.environ.get("RUNPOD_NETWORK_VOLUME_ID")
    
    if not all([access_key_id, secret_access_key, datacenter, network_volume_id]):
        raise ValueError(
            "Missing required environment variables. Please set:\n"
            "- RUNPOD_S3_ACCESS_KEY_ID\n"
            "- RUNPOD_S3_SECRET_ACCESS_KEY\n"
            "- RUNPOD_DATACENTER\n"
            "- RUNPOD_NETWORK_VOLUME_ID"
        )
    
    return RunPodS3Storage(
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        datacenter=datacenter,
        network_volume_id=network_volume_id
    ) 