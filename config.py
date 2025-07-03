import os

# Bot Configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'your_bot_token_here')

# FFmpeg options for audio playback
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# YouTube-DL options
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'cookiefile': None,
    'extractor_args': {
        'youtube': {
            'player_client': ['android'],
            'player_skip': ['webpage'],
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
    }
}

# Bot Settings
MAX_QUEUE_SIZE = 50
MAX_SONG_DURATION = 3600  # 1 hour in seconds
COMMAND_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'discord_bot.log'

# Voice Settings
VOICE_TIMEOUT = 300  # 5 minutes of inactivity before auto-disconnect
