import logging
import discord
from typing import Union

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('discord_bot.log', encoding='utf-8')
        ]
    )
    
    # Set discord.py logging level to WARNING to reduce noise
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)
    
    # Set yt-dlp logging level to ERROR to reduce noise
    yt_dlp_logger = logging.getLogger('yt_dlp')
    yt_dlp_logger.setLevel(logging.ERROR)

def is_admin(user: Union[discord.Member, discord.User]) -> bool:
    """Check if user has administrator permissions"""
    if isinstance(user, discord.Member):
        return user.guild_permissions.administrator
    return False

def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS format"""
    if seconds < 3600:  # Less than 1 hour
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    else:  # 1 hour or more
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def validate_youtube_url(url: str) -> bool:
    """Validate if the URL is a valid YouTube URL"""
    youtube_domains = [
        'youtube.com',
        'youtu.be',
        'www.youtube.com',
        'm.youtube.com',
        'music.youtube.com'
    ]
    
    return any(domain in url.lower() for domain in youtube_domains)

def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed"""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=0xe74c3c
    )
    return embed

def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized success embed"""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=0x2ecc71
    )
    return embed

def create_info_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized info embed"""
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=0x3498db
    )
    return embed
