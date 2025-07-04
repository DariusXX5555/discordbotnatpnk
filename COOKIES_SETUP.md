# YouTube Cookies Setup

Your bot is configured to use YouTube cookies to bypass bot detection. Here's how to set them up:

## Method 1: Browser Extension (Easiest)

1. **Install "Get cookies.txt LOCALLY" extension** in Chrome/Firefox
2. **Go to YouTube.com** and make sure you're logged in
3. **Click the extension** and export cookies
4. **Save as `cookies.txt`** in your project folder
5. **Upload to GitHub** with your other files

## Method 2: Manual Export (Advanced)

1. **Open YouTube in browser** (logged in)
2. **Open Developer Tools** (F12)
3. **Go to Application/Storage tab**
4. **Copy cookies** in Netscape format
5. **Save as `cookies.txt`**

## Method 3: Use yt-dlp Command (If you have yt-dlp installed)

```bash
yt-dlp --cookies-from-browser chrome --write-info-json --skip-download "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## File Location

Place `cookies.txt` in your project root folder (same level as main.py).

## Security Note

- Cookies contain your YouTube session data
- Keep them private (add to .gitignore if concerned)
- They expire after some time and need refreshing

## Fallback

If cookies don't work, the bot will use the local music system instead. Add your audio files to the `music/` folder and use `/songs` to see available music.