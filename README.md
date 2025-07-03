# Discord Music Bot

A Discord bot that plays music from YouTube in voice channels with administrator-only commands.

## Features

- `/join "channel"` - Join a voice channel (admin only)
- `/leave` - Leave the current voice channel (admin only)
- `/music "link"` - Play music from YouTube (admin only)
- `/skip` - Skip the current song (admin only)
- `/queue` - Show the current music queue
- `/truth` - Get a random Bible verse (available to everyone)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your Discord bot token:**
   - Set environment variable: `DISCORD_BOT_TOKEN=your_token_here`
   - Or edit `config.py` to add your token directly

3. **Run the bot:**
   ```bash
   python main.py
   ```

## Deployment

### Railway (Recommended)
1. Upload files to GitHub
2. Connect GitHub repo to Railway
3. Add `DISCORD_BOT_TOKEN` environment variable
4. Deploy automatically

### Other Platforms
- Render.com
- Fly.io
- Heroku
- Self-hosting on VPS

## Requirements

- Python 3.8+
- FFmpeg (for audio processing)
- Discord bot token
- Administrator permissions in Discord server

## Files

- `main.py` - Main bot code with commands
- `config.py` - Configuration settings
- `music_player.py` - Music playback handling
- `utils.py` - Helper functions
- `requirements.txt` - Python dependencies

## Notes

- Only users with administrator permissions can use commands
- Bot supports YouTube links and handles playlists
- Designed for 24/7 hosting on cloud platforms
- Voice connections work best outside of sandboxed environments