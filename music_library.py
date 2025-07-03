"""
Music library management for local audio files
"""
import os
import random
from typing import List, Dict, Optional

class MusicLibrary:
    """Manages local music files and provides selection interface"""
    
    def __init__(self, music_directory: str = "music"):
        self.music_directory = music_directory
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        self.music_files = self._scan_music_files()
        
    def _scan_music_files(self) -> Dict[str, str]:
        """Scan music directory for supported audio files"""
        music_files = {}
        
        if not os.path.exists(self.music_directory):
            os.makedirs(self.music_directory)
            return music_files
            
        for filename in os.listdir(self.music_directory):
            if any(filename.lower().endswith(ext) for ext in self.supported_formats):
                # Use filename without extension as display name
                display_name = os.path.splitext(filename)[0]
                file_path = os.path.join(self.music_directory, filename)
                music_files[display_name] = file_path
                
        return music_files
    
    def get_music_list(self) -> List[str]:
        """Get list of available music files"""
        return list(self.music_files.keys())
    
    def get_file_path(self, song_name: str) -> Optional[str]:
        """Get file path for a song name"""
        return self.music_files.get(song_name)
    
    def get_random_song(self) -> Optional[Dict[str, str]]:
        """Get a random song from the library"""
        if not self.music_files:
            return None
            
        song_name = random.choice(list(self.music_files.keys()))
        return {
            'name': song_name,
            'path': self.music_files[song_name]
        }
    
    def refresh_library(self):
        """Refresh the music library (rescan files)"""
        self.music_files = self._scan_music_files()
    
    def add_default_songs(self):
        """Add some default Christian/worship songs information"""
        default_songs = [
            "Amazing Grace",
            "How Great Thou Art",
            "Blessed Assurance",
            "Great Is Thy Faithfulness",
            "Holy Holy Holy",
            "It Is Well With My Soul",
            "Jesus Loves Me",
            "When Peace Like A River",
            "Crown Him With Many Crowns",
            "Praise God From Whom All Blessings Flow"
        ]
        
        readme_content = """# Music Library

## How to Add Songs

1. Add your audio files (.mp3, .wav, .m4a, .ogg, .flac) to this music folder
2. The bot will automatically detect them
3. Use the song filename (without extension) in the /music command

## Suggested Christian/Worship Songs

Here are some beautiful Christian songs you might want to add:

"""
        
        for song in default_songs:
            readme_content += f"- {song}\n"
            
        readme_content += """
## Finding Music

You can find royalty-free Christian music from:
- Christian Commons (creative commons licensed)
- Public domain hymns
- Your own recorded music
- Licensed music you own

## File Naming

- Use clear, simple names
- Avoid special characters
- Example: "Amazing Grace.mp3"
"""
        
        readme_path = os.path.join(self.music_directory, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)