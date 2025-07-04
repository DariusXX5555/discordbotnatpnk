# Manual FFmpeg Installation for GitHub

## Step 1: Download FFmpeg Binary

1. Go to https://github.com/BtbN/FFmpeg-Builds/releases
2. Download `ffmpeg-master-latest-win64-gpl.zip` (for Windows) or `ffmpeg-master-latest-linux64-gpl.tar.xz` (for Linux)
3. Extract the downloaded file
4. Find the `ffmpeg.exe` (Windows) or `ffmpeg` (Linux) file inside the `bin` folder

## Step 2: Add to Your GitHub Repository

1. In your GitHub repository, create a folder called `ffmpeg-bin`
2. Upload the `ffmpeg.exe` or `ffmpeg` file to this folder
3. The file path should be: `ffmpeg-bin/ffmpeg.exe` or `ffmpeg-bin/ffmpeg`

## Step 3: Files Structure

Your GitHub repository should look like this:
```
your-repo/
├── ffmpeg-bin/
│   └── ffmpeg.exe (or ffmpeg)
├── main.py
├── music_player.py
├── requirements.txt
└── other files...
```

## Step 4: Railway Deployment

Set Railway start command to: `python main.py`

The bot will automatically find and use your manually uploaded FFmpeg binary.