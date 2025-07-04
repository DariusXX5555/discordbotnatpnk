import discord
import asyncio
import yt_dlp
import logging
import os
import shutil
from typing import Dict, List, Optional, Any
from config import FFMPEG_OPTIONS, YDL_OPTIONS
from music_library import MusicLibrary

logger = logging.getLogger(__name__)

def find_ffmpeg():
    """Find FFmpeg executable on the system"""
    # Check manual installation in ffmpeg-bin folder (for GitHub upload)
    manual_paths = [
        './ffmpeg-bin/ffmpeg.exe',  # Windows
        './ffmpeg-bin/ffmpeg',      # Linux
        './bin/ffmpeg'              # Local installation
    ]
    
    for path in manual_paths:
        if os.path.exists(path):
            return path
    
    # Try shutil.which first (checks PATH)
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path
    
    # Try common system locations
    system_paths = [
        '/usr/bin/ffmpeg',           # Standard Linux
        '/usr/local/bin/ffmpeg',     # Manual install
        '/bin/ffmpeg',               # Some distros
        '/opt/ffmpeg/bin/ffmpeg',    # Custom install
    ]
    
    for path in system_paths:
        if os.path.exists(path):
            return path
    
    # Try to find in /nix/store (for Replit/NixOS)
    if os.path.exists('/nix/store'):
        for root, dirs, files in os.walk('/nix/store'):
            if 'ffmpeg' in files and 'bin' in root:
                candidate = os.path.join(root, 'ffmpeg')
                if os.path.exists(candidate):
                    return candidate
    
    # Default fallback
    return 'ffmpeg'

class MusicPlayer:
    """Handles music playback for a Discord voice client"""
    
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.queue: List[Dict[str, Any]] = []
        self.current_song: Optional[Dict[str, Any]] = None
        self.is_playing_flag = False
        self.skip_flag = False
        self.music_library = MusicLibrary()
        
    async def add_to_queue(self, input_str: str) -> Dict[str, Any]:
        """Add a song to the queue (local file name or YouTube URL)"""
        try:
            # Check if it's a local file first
            local_path = self.music_library.get_file_path(input_str)
            if local_path and os.path.exists(local_path):
                return await self._add_local_file(input_str, local_path)
            
            # Otherwise, try as YouTube URL
            return await self._add_youtube_url(input_str)
                
        except Exception as e:
            logger.error(f"Error adding song to queue: {str(e)}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    async def _add_local_file(self, song_name: str, file_path: str) -> Dict[str, Any]:
        """Add a local file to the queue"""
        song_info = {
            'title': song_name,
            'url': file_path,
            'webpage_url': file_path,
            'duration': 0,  # Could be calculated with mutagen library
            'uploader': 'Local Library',
            'is_local': True
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
    
    async def _add_youtube_url(self, url: str) -> Dict[str, Any]:
        """Add a YouTube URL to the queue"""
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
                    'is_local': False
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
                    
                    # Create audio source with proper error handling
                    try:
                        # Find FFmpeg executable
                        ffmpeg_executable = find_ffmpeg()
                        
                        # For local files, use direct path
                        if self.current_song.get('is_local', False):
                            audio_source = discord.FFmpegPCMAudio(
                                self.current_song['url'],
                                executable=ffmpeg_executable,
                                options='-vn'
                            )
                        else:
                            # For streaming URLs, use full options
                            ffmpeg_opts = dict(FFMPEG_OPTIONS)
                            ffmpeg_opts['executable'] = ffmpeg_executable
                            audio_source = discord.FFmpegPCMAudio(
                                stream_url,
                                **ffmpeg_opts
                            )
                        
                        # Play audio
                        self.voice_client.play(
                            audio_source,
                            after=lambda e: asyncio.run_coroutine_threadsafe(
                                self._after_playing(e), 
                                self.voice_client.loop
                            )
                        )
                        
                    except Exception as audio_error:
                        logger.error(f'Error creating audio source: {audio_error}')
                        await self._play_next()
                        return
                    
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
    
    def get_available_songs(self) -> List[str]:
        """Get list of available local songs"""
        return self.music_library.get_music_list()
    
    def refresh_music_library(self):
        """Refresh the music library"""
        self.music_library.refresh_library()
    
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
