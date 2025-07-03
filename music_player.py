import discord
import asyncio
import yt_dlp
import logging
from typing import Dict, List, Optional, Any
from config import FFMPEG_OPTIONS, YDL_OPTIONS

logger = logging.getLogger(__name__)

class MusicPlayer:
    """Handles music playback for a Discord voice client"""
    
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.queue: List[Dict[str, Any]] = []
        self.current_song: Optional[Dict[str, Any]] = None
        self.is_playing_flag = False
        self.skip_flag = False
        
    async def add_to_queue(self, url: str) -> Dict[str, Any]:
        """Add a song to the queue"""
        try:
            # Extract video info
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    
                    # Handle playlists
                    if 'entries' in info:
                        if info['entries']:
                            # Take the first video from playlist
                            info = info['entries'][0]
                        else:
                            return {'success': False, 'error': 'Empty playlist'}
                    
                    # Check duration - limit to 10 minutes for testing
                    duration = info.get('duration', 0)
                    if duration > 600:  # 10 minutes
                        return {'success': False, 'error': 'Song too long (max 10 minutes for testing)'}
                    
                    # Extract required information
                    song_info = {
                        'title': info.get('title', 'Unknown Title'),
                        'url': info.get('url', ''),
                        'webpage_url': info.get('webpage_url', url),
                        'duration': duration,
                        'uploader': info.get('uploader', 'Unknown'),
                    }
                    
                    # Clear queue and add only this song for single playback
                    self.queue.clear()
                    self.queue.append(song_info)
                    
                    # If nothing is playing, start playing
                    if not self.is_playing_flag:
                        await self._play_next()
                        return {'success': True, 'title': song_info['title'], 'position': 0}
                    else:
                        # Stop current and play new
                        self.skip_flag = True
                        self.voice_client.stop()
                        return {'success': True, 'title': song_info['title'], 'position': 0}
                    
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e)
                    if "Sign in to confirm" in error_msg:
                        return {'success': False, 'error': 'YouTube blocked this request. Try a different video or use a direct link.'}
                    elif "Video unavailable" in error_msg:
                        return {'success': False, 'error': 'Video is unavailable or private'}
                    elif "blocked" in error_msg.lower():
                        return {'success': False, 'error': 'Video is blocked in your region'}
                    else:
                        return {'success': False, 'error': f'YouTube access issue: Try a different video'}
                        
        except Exception as e:
            logger.error(f'Error adding to queue: {e}')
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    async def _play_next(self):
        """Play the next song in the queue"""
        try:
            if not self.queue:
                self.is_playing_flag = False
                self.current_song = None
                return
            
            # Get next song
            self.current_song = self.queue.pop(0)
            self.is_playing_flag = True
            self.skip_flag = False
            
            # Get fresh URL for streaming
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                try:
                    info = ydl.extract_info(self.current_song['webpage_url'], download=False)
                    
                    # Handle playlists
                    if 'entries' in info:
                        if info['entries']:
                            info = info['entries'][0]
                        else:
                            await self._play_next()
                            return
                    
                    stream_url = info.get('url')
                    if not stream_url:
                        logger.error(f'No stream URL found for: {self.current_song["title"]}')
                        await self._play_next()
                        return
                    
                    # Create audio source
                    audio_source = discord.FFmpegPCMAudio(
                        stream_url,
                        **FFMPEG_OPTIONS
                    )
                    
                    # Play audio
                    self.voice_client.play(
                        audio_source,
                        after=lambda e: asyncio.run_coroutine_threadsafe(
                            self._after_playing(e), 
                            self.voice_client.loop
                        )
                    )
                    
                    logger.info(f'Started playing: {self.current_song["title"]}')
                    
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f'Error getting stream URL: {e}')
                    await self._play_next()
                    return
                    
        except Exception as e:
            logger.error(f'Error in _play_next: {e}')
            self.is_playing_flag = False
            self.current_song = None
    
    async def _after_playing(self, error):
        """Called after a song finishes playing"""
        if error:
            logger.error(f'Player error: {error}')
        
        # Only play next if not manually skipped
        if not self.skip_flag:
            await self._play_next()
    
    def skip(self):
        """Skip the current song"""
        if self.voice_client.is_playing():
            self.skip_flag = True
            self.voice_client.stop()
    
    def is_playing(self) -> bool:
        """Check if music is currently playing"""
        return self.voice_client.is_playing()
    
    def get_queue_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current queue"""
        if not self.current_song and not self.queue:
            return None
        
        return {
            'current': self.current_song['title'] if self.current_song else None,
            'upcoming': [song['title'] for song in self.queue]
        }
    
    async def cleanup(self):
        """Cleanup the music player"""
        try:
            if self.voice_client.is_playing():
                self.voice_client.stop()
            
            self.queue.clear()
            self.current_song = None
            self.is_playing_flag = False
            self.skip_flag = False
            
            logger.info('Music player cleaned up')
            
        except Exception as e:
            logger.error(f'Error during cleanup: {e}')
