#!/usr/bin/env python3
"""
Script to download and install FFmpeg on Railway deployment
"""
import os
import urllib.request
import tarfile
import shutil
import sys

def download_ffmpeg():
    """Download and install FFmpeg"""
    if os.path.exists('./bin/ffmpeg'):
        print("FFmpeg already exists, skipping download")
        return True
    
    print("Downloading FFmpeg...")
    try:
        # Download FFmpeg
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        urllib.request.urlretrieve(url, "ffmpeg.tar.xz")
        
        # Extract
        with tarfile.open("ffmpeg.tar.xz", "r:xz") as tar:
            tar.extractall()
        
        # Find extracted directory
        for item in os.listdir("."):
            if item.startswith("ffmpeg-") and os.path.isdir(item):
                # Create bin directory
                os.makedirs("bin", exist_ok=True)
                
                # Copy ffmpeg
                shutil.copy2(os.path.join(item, "ffmpeg"), "bin/ffmpeg")
                os.chmod("bin/ffmpeg", 0o755)
                
                # Cleanup
                shutil.rmtree(item)
                os.remove("ffmpeg.tar.xz")
                
                print("FFmpeg installed successfully!")
                return True
        
        print("Error: Could not find FFmpeg in extracted files")
        return False
        
    except Exception as e:
        print(f"Error downloading FFmpeg: {e}")
        return False

if __name__ == "__main__":
    success = download_ffmpeg()
    sys.exit(0 if success else 1)