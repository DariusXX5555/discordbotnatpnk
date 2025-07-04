#!/usr/bin/env python3
"""
Railway startup script - downloads FFmpeg and starts the Discord bot
"""
import os
import subprocess
import sys
import urllib.request
import tarfile
import shutil

def download_ffmpeg():
    """Download FFmpeg for Railway deployment"""
    print("Checking for FFmpeg...")
    
    # Check if already installed
    if os.path.exists('./ffmpeg-bin/ffmpeg'):
        print("FFmpeg already exists")
        return True
    
    try:
        print("Downloading FFmpeg...")
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        urllib.request.urlretrieve(url, "ffmpeg.tar.xz")
        
        print("Extracting FFmpeg...")
        with tarfile.open("ffmpeg.tar.xz", "r:xz") as tar:
            tar.extractall()
        
        # Find the extracted directory
        extracted_dir = None
        for item in os.listdir("."):
            if item.startswith("ffmpeg-") and os.path.isdir(item):
                extracted_dir = item
                break
        
        if extracted_dir:
            # Create ffmpeg-bin directory
            os.makedirs("ffmpeg-bin", exist_ok=True)
            
            # Copy ffmpeg binary
            src = os.path.join(extracted_dir, "ffmpeg")
            dst = "./ffmpeg-bin/ffmpeg"
            shutil.copy2(src, dst)
            os.chmod(dst, 0o755)
            
            # Cleanup
            shutil.rmtree(extracted_dir)
            os.remove("ffmpeg.tar.xz")
            
            print("FFmpeg installed successfully!")
            return True
        else:
            print("Could not find FFmpeg in extracted files")
            return False
            
    except Exception as e:
        print(f"Error installing FFmpeg: {e}")
        return False

def main():
    """Main function"""
    # Download FFmpeg
    if not download_ffmpeg():
        print("Failed to install FFmpeg, but continuing anyway...")
    
    # Start the Discord bot
    print("Starting Discord bot...")
    os.execv(sys.executable, [sys.executable, "main.py"])

if __name__ == "__main__":
    main()