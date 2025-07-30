# src/handler.py
import runpod
import os
import sys
import torch
from pathlib import Path

# Add the workspace to Python path
sys.path.append('/workspace')

def load_model():
    """Load the HunyuanVideo-Avatar model"""
    try:
        print("Loading HunyuanVideo-Avatar model...")
        
        # Check for models in RunPod network volume first, then fallback to container
        network_volume_dir = Path("/runpod-volume/weights")
        container_weights_dir = Path("/workspace/HunyuanVideo-Avatar/weights")
        
        # Determine which weights directory to use
        if network_volume_dir.exists() and (network_volume_dir / "ckpts").exists():
            weights_dir = network_volume_dir
            print(f"✅ Using models from RunPod network volume: {weights_dir}")
        elif container_weights_dir.exists() and (container_weights_dir / "ckpts").exists():
            weights_dir = container_weights_dir
            print(f"✅ Using models from container: {weights_dir}")
        else:
            # Download models to network volume
            print("📥 Models not found. Downloading to RunPod network volume...")
            weights_dir = network_volume_dir
            weights_dir.mkdir(parents=True, exist_ok=True)
            
            # Download models with progress monitoring
            import subprocess
            import sys
            
            print("🔄 Starting model download (this may take 10-60 minutes)...")
            print("📊 Download progress will be shown below:")
            
            # Run huggingface-cli download with progress
            process = subprocess.Popen([
                "huggingface-cli", "download", 
                "tencent/HunyuanVideo-Avatar", 
                "--local-dir", str(weights_dir)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Stream the output in real-time
            for line in process.stdout:
                print(f"📥 {line.strip()}")
                sys.stdout.flush()
            
            process.wait()
            
            if process.returncode != 0:
                raise Exception("Model download failed")
            
            print("✅ Model download completed!")
        
        # Check for key model files
        ckpts_dir = weights_dir / "ckpts"
        if not ckpts_dir.exists():
            raise FileNotFoundError("Model checkpoints not found in weights/ckpts/")
        
        print(f"✅ Models found in: {weights_dir}")
        print(f"📁 Available model directories:")
        for item in ckpts_dir.iterdir():
            if item.is_dir():
                print(f"  - {item.name}")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 Using device: {device}")
        
        # Import HunyuanVideo-Avatar modules
        from models.hunyuan_video_avatar import HunyuanVideoAvatar
        from configs.config import get_config
        
        # Load configuration
        config = get_config()
        config.device = device
        
        # Initialize model
        model = HunyuanVideoAvatar(config)
        model.to(device)
        model.eval()
        
        print("✅ Model loaded successfully!")
        return model
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

def generate_video(job):
    """
    Generate video based on the job input using HunyuanVideo-Avatar
    """
    job_input = job["input"]
    
    # Extract parameters from job input
    prompt = job_input.get("prompt", "")
    duration = job_input.get("duration", 5)
    fps = job_input.get("fps", 24)
    resolution = job_input.get("resolution", "704x704")  # Default to 704x704 for better quality
    seed = job_input.get("seed", 128)
    cfg_scale = job_input.get("cfg_scale", 7.5)
    infer_steps = job_input.get("infer_steps", 50)
    
    try:
        # Set up environment variables for HunyuanVideo-Avatar
        os.environ['PYTHONPATH'] = '/workspace'
        os.environ['MODEL_BASE'] = '/runpod-volume/weights'
        os.environ['DISABLE_SP'] = '1'  # Disable multi-GPU processing
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        
        # Create output directory
        output_dir = f"/workspace/results/job_{job['id']}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create input CSV file for HunyuanVideo-Avatar
        csv_path = f"{output_dir}/input.csv"
        with open(csv_path, 'w') as f:
            f.write("prompt,seed\n")
            f.write(f'"{prompt}",{seed}\n')
        
        # Determine checkpoint path
        checkpoint_path = "/runpod-volume/weights/ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states_fp8.pt"
        
        # Calculate frames based on duration and fps
        sample_n_frames = int(duration * fps)
        
        # Parse resolution
        if "x" in resolution:
            width, height = map(int, resolution.split("x"))
            image_size = max(width, height)  # Use the larger dimension
        else:
            image_size = 704  # Default size
        
        # Build the command arguments
        cmd_args = [
            "python3", "hymm_sp/sample_gpu_poor.py",
            "--input", csv_path,
            "--ckpt", checkpoint_path,
            "--sample-n-frames", str(sample_n_frames),
            "--seed", str(seed),
            "--image-size", str(image_size),
            "--cfg-scale", str(cfg_scale),
            "--infer-steps", str(infer_steps),
            "--use-deepcache", "1",
            "--flow-shift-eval-video", "5.0",
            "--save-path", output_dir,
            "--use-fp8",
            "--infer-min"
        ]
        
        print(f"🎬 Starting video generation with parameters:")
        print(f"   Prompt: {prompt}")
        print(f"   Duration: {duration}s")
        print(f"   FPS: {fps}")
        print(f"   Resolution: {resolution}")
        print(f"   Frames: {sample_n_frames}")
        print(f"   Image Size: {image_size}")
        print(f"   Output Dir: {output_dir}")
        
        # Execute the HunyuanVideo-Avatar inference
        import subprocess
        import sys
        
        print("🚀 Executing HunyuanVideo-Avatar inference...")
        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd="/workspace"
        )
        
        # Stream the output in real-time
        for line in process.stdout:
            print(f"📹 {line.strip()}")
            sys.stdout.flush()
        
        process.wait()
        
        if process.returncode != 0:
            raise Exception(f"HunyuanVideo-Avatar inference failed with return code {process.returncode}")
        
        # Find the generated video file
        video_files = list(Path(output_dir).glob("*.mp4"))
        if not video_files:
            raise FileNotFoundError(f"No video files found in {output_dir}")
        
        output_video = video_files[0]
        print(f"✅ Video generated successfully: {output_video}")
        
        # Return the result
        return {
            "status": "success",
            "output_url": str(output_video),
            "metadata": {
                "prompt": prompt,
                "duration": duration,
                "fps": fps,
                "resolution": resolution,
                "seed": seed,
                "cfg_scale": cfg_scale,
                "infer_steps": infer_steps,
                "frames": sample_n_frames,
                "image_size": image_size
            }
        }
        
    except Exception as e:
        print(f"❌ Error generating video: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def handler(job):
    """
    RunPod handler function
    """
    try:
        # Process the job directly using HunyuanVideo-Avatar script
        result = generate_video(job)
        return result
        
    except Exception as e:
        return {"error": f"Handler error: {str(e)}"}

if __name__ == "__main__":
    # Start the RunPod serverless handler
    runpod.serverless.start({"handler": handler})