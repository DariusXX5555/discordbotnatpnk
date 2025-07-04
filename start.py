#!/usr/bin/env python3
"""
Startup script for Railway deployment - installs FFmpeg then starts bot
"""
import subprocess
import sys
import os

def main():
    """Main startup function"""
    # Install FFmpeg if not present
    if not os.path.exists('./bin/ffmpeg'):
        print("Installing FFmpeg...")
        result = subprocess.run([sys.executable, 'install_ffmpeg.py'])
        if result.returncode != 0:
            print("Failed to install FFmpeg")
            sys.exit(1)
    
    # Start the Discord bot
    print("Starting Discord bot...")
    subprocess.run([sys.executable, 'main.py'])

if __name__ == "__main__":
    main()