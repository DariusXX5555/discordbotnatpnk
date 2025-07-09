import discord
from discord.ext import commands
import asyncio
import logging
import os
import random
import aiohttp
import json
from datetime import datetime
from config import BOT_TOKEN, FFMPEG_OPTIONS
from music_player import MusicPlayer
from utils import is_admin, setup_logging, create_error_embed, create_info_embed, create_success_embed

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Music players for each guild
music_players = {}

# Bible verses for /truth command
BIBLE_VERSES = [
    "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life. - John 3:16",
    "Trust in the Lord with all your heart and lean not on your own understanding. - Proverbs 3:5",
    "I can do all things through Christ who strengthens me. - Philippians 4:13",
    "The Lord is my shepherd, I lack nothing. - Psalm 23:1",
    "Be strong and courageous. Do not be afraid; do not be discouraged, for the Lord your God will be with you wherever you go. - Joshua 1:9",
    "And we know that in all things God works for the good of those who love him. - Romans 8:28",
    "Cast all your anxiety on him because he cares for you. - 1 Peter 5:7",
    "The Lord your God is with you, the Mighty Warrior who saves. - Zephaniah 3:17",
    "Peace I leave with you; my peace I give you. I do not give to you as the world gives. - John 14:27",
    "But those who hope in the Lord will renew their strength. They will soar on wings like eagles. - Isaiah 40:31",
    "Be still, and know that I am God. - Psalm 46:10",
    "The Lord is close to the brokenhearted and saves those who are crushed in spirit. - Psalm 34:18",
    "Do not fear, for I am with you; do not be dismayed, for I am your God. - Isaiah 41:10",
    "Love is patient, love is kind. It does not envy, it does not boast, it is not proud. - 1 Corinthians 13:4",
    "But seek first his kingdom and his righteousness, and all these things will be given to you as well. - Matthew 6:33",
    "In their hearts humans plan their course, but the Lord establishes their steps. - Proverbs 16:9",
    "The name of the Lord is a fortified tower; the righteous run to it and are safe. - Proverbs 18:10",
    "Therefore, if anyone is in Christ, the new creation has come: The old has gone, the new is here! - 2 Corinthians 5:17",
    "Let your light shine before others, that they may see your good deeds and glorify your Father in heaven. - Matthew 5:16",
    "Come to me, all you who are weary and burdened, and I will give you rest. - Matthew 11:28",
    "Draw near to God, and he will draw near to you. - James 4:8",
    "Delight yourself in the Lord, and he will give you the desires of your heart. - Psalm 37:4",
    "If we confess our sins, he is faithful and just and will forgive us our sins and purify us from all unrighteousness. - 1 John 1:9",
    "Therefore confess your sins to each other and pray for each other so that you may be healed. - James 5:16",
    "Remain in me, as I also remain in you. No branch can bear fruit by itself; it must remain in the vine. - John 15:4",
    "But when you pray, go into your room, close the door and pray to your Father, who is unseen. - Matthew 6:6",
    "All Scripture is God-breathed and is useful for teaching, rebuking, correcting and training in righteousness. - 2 Timothy 3:16",
    "Your word is a lamp for my feet, a light on my path. - Psalm 119:105",
    "Seek the Lord while he may be found; call on him while he is near. - Isaiah 55:6",
    "And without faith it is impossible to please God, because anyone who comes to him must believe that he exists. - Hebrews 11:6",
    "Take delight in the Lord, and he will give you the desires of your heart. Commit your way to the Lord; trust in him. - Psalm 37:4-5",
    "Submit yourselves, then, to God. Resist the devil, and he will flee from you. - James 4:7",
    "Be transformed by the renewing of your mind. Then you will be able to test and approve what God's will is. - Romans 12:2",
    "Let us hold unswervingly to the hope we profess, for he who promised is faithful. - Hebrews 10:23",
    "Therefore, I urge you, brothers and sisters, in view of God's mercy, to offer your bodies as a living sacrifice. - Romans 12:1",
    "Whoever wants to be my disciple must deny themselves and take up their cross and follow me. - Matthew 16:24",
    "Ask and it will be given to you; seek and you will find; knock and the door will be opened to you. - Matthew 7:7",
    "The fear of the Lord is the beginning of wisdom, and knowledge of the Holy One is understanding. - Proverbs 9:10",
    "God is faithful, who will not allow you to be tempted beyond what you are able. - 1 Corinthians 10:13",
    "Therefore encourage one another and build each other up, just as in fact you are doing. - 1 Thessalonians 5:11"
]

# Fun facts for random facts command
FUN_FACTS = [
    "A group of flamingos is called a 'flamboyance'.",
    "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
    "Octopuses have three hearts and blue blood.",
    "A cloud can weigh more than a million pounds.",
    "Bananas are berries, but strawberries aren't.",
    "The human brain uses about 20% of the body's total energy.",
    "There are more possible games of chess than atoms in the observable universe.",
    "A group of owls is called a 'parliament'.",
    "The shortest war in history lasted only 38-45 minutes.",
    "A shrimp's heart is in its head.",
    "The Great Wall of China isn't visible from space without aid.",
    "Dolphins have names for each other.",
    "A group of pandas is called an 'embarrassment'.",
    "The human body produces about 25 million new cells every second.",
    "Lightning strikes the Earth about 100 times per second.",
    "A group of crows is called a 'murder'.",
    "The average person walks past 36 murderers in their lifetime.",
    "A group of jellyfish is called a 'smack'.",
    "The heart of a blue whale is so large that a human could crawl through its arteries.",
    "A group of unicorns is called a 'blessing'."
]

# Jokes for the joke command
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "Why don't eggs tell jokes? They'd crack each other up!",
    "What do you call a fake noodle? An impasta!",
    "Why did the scarecrow win an award? He was outstanding in his field!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why don't skeletons fight each other? They don't have the guts!",
    "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks!",
    "Why did the math book look so sad? Because it had too many problems!",
    "What do you call a sleeping bull? A bulldozer!",
    "Why don't scientists trust stairs? Because they're always up to something!",
    "What do you call a fish wearing a crown? A king fish!",
    "Why did the cookie go to the doctor? Because it felt crumbly!",
    "What do you call a pig that does karate? A pork chop!",
    "Why don't elephants use computers? They're afraid of the mouse!"
]

# 8-ball responses
EIGHT_BALL_RESPONSES = [
    "It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
    "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
    "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
    "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
    "Don't count on it", "My reply is no", "My sources say no",
    "Outlook not so good", "Very doubtful"
]

# Would you rather questions
WOULD_YOU_RATHER = [
    "Would you rather have the ability to fly or be invisible?",
    "Would you rather live in the past or the future?",
    "Would you rather have super strength or super intelligence?",
    "Would you rather be able to read minds or predict the future?",
    "Would you rather never have to sleep or never have to eat?",
    "Would you rather be famous or be the best friend of someone famous?",
    "Would you rather live forever or live a perfect life for 50 years?",
    "Would you rather have unlimited money or unlimited time?",
    "Would you rather be able to speak every language or play every instrument?",
    "Would you rather live in a world without music or without movies?",
    "Would you rather always be hot or always be cold?",
    "Would you rather have telepathy or teleportation?",
    "Would you rather be the smartest person alive or the most attractive?",
    "Would you rather have dinner with anyone from history or anyone alive today?",
    "Would you rather be able to control fire or water?"
]

# Trivia questions with answers
TRIVIA_QUESTIONS = [
    {"question": "What is the capital of Australia?", "answer": "Canberra", "options": ["Sydney", "Melbourne", "Canberra", "Perth"]},
    {"question": "Which planet is closest to the Sun?", "answer": "Mercury", "options": ["Venus", "Mercury", "Mars", "Earth"]},
    {"question": "What is the largest ocean on Earth?", "answer": "Pacific", "options": ["Atlantic", "Indian", "Arctic", "Pacific"]},
    {"question": "Who painted the Mona Lisa?", "answer": "Leonardo da Vinci", "options": ["Van Gogh", "Picasso", "Leonardo da Vinci", "Michelangelo"]},
    {"question": "What is the chemical symbol for gold?", "answer": "Au", "options": ["Go", "Au", "Ag", "Al"]},
    {"question": "Which country has the most time zones?", "answer": "France", "options": ["Russia", "USA", "China", "France"]},
    {"question": "What is the smallest country in the world?", "answer": "Vatican City", "options": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"]},
    {"question": "How many hearts does an octopus have?", "answer": "3", "options": ["2", "3", "4", "5"]},
    {"question": "What is the hardest natural substance on Earth?", "answer": "Diamond", "options": ["Quartz", "Diamond", "Granite", "Steel"]},
    {"question": "Which mammal is known to have the most powerful bite?", "answer": "Hippopotamus", "options": ["Lion", "Shark", "Crocodile", "Hippopotamus"]}
]

# Quote categories
INSPIRATIONAL_QUOTES = [
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Life is what happens to you while you're busy making other plans. - John Lennon",
    "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
    "It is during our darkest moments that we must focus to see the light. - Aristotle",
    "The only impossible journey is the one you never begin. - Tony Robbins",
    "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
    "The way to get started is to quit talking and begin doing. - Walt Disney",
    "Don't let yesterday take up too much of today. - Will Rogers",
    "You learn more from failure than from success. Don't let it stop you. - Unknown",
    "If you are working on something that you really care about, you don't have to be pushed. - Steve Jobs"
]

# Server activity tracking
server_stats = {}

# Rock Paper Scissors game state
rps_games = {}

@bot.event
async def on_ready():
    """Called when bot is ready"""
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

@bot.event
async def on_guild_join(guild):
    """Called when bot joins a guild"""
    logger.info(f'Joined guild: {guild.name} ({guild.id})')

@bot.event
async def on_guild_remove(guild):
    """Called when bot leaves a guild"""
    logger.info(f'Left guild: {guild.name} ({guild.id})')
    # Cleanup music player
    if guild.id in music_players:
        await music_players[guild.id].cleanup()
        del music_players[guild.id]

@bot.tree.command(name="join", description="Join a voice channel")
async def join(interaction: discord.Interaction, channel: str):
    """Join a voice channel"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        # Defer response as voice operations can take time
        await interaction.response.defer()

        # Find the voice channel
        voice_channel = None
        for ch in interaction.guild.voice_channels:
            if ch.name.lower() == channel.lower():
                voice_channel = ch
                break

        if not voice_channel:
            await interaction.followup.send(f"❌ Voice channel '{channel}' not found.")
            return

        # Check if bot is already in a voice channel
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel.id == voice_channel.id:
                await interaction.followup.send(f"✅ Already connected to {voice_channel.name}")
                return
            else:
                await interaction.guild.voice_client.disconnect()

        # Connect to voice channel
        try:
            voice_client = await voice_channel.connect(timeout=60.0, reconnect=True)
            logger.info(f'Connected to voice channel: {voice_channel.name} in guild: {interaction.guild.name}')
            
            # Initialize music player for this guild
            if interaction.guild.id not in music_players:
                music_players[interaction.guild.id] = MusicPlayer(voice_client)
            else:
                music_players[interaction.guild.id].voice_client = voice_client

            await interaction.followup.send(f"✅ Connected to {voice_channel.name}")

        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Connection timed out. This may be due to network restrictions in the hosting environment. The bot works best when self-hosted or on a VPS.")
            logger.error(f'Connection timeout for voice channel: {voice_channel.name}')
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to connect to voice channel. Error: {str(e)}")
            logger.error(f'Failed to connect to voice channel: {e}')

    except Exception as e:
        logger.error(f'Error in join command: {e}')
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")

@bot.tree.command(name="leave", description="Leave the current voice channel")
async def leave(interaction: discord.Interaction):
    """Leave the current voice channel"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

        # Cleanup music player
        if interaction.guild.id in music_players:
            await music_players[interaction.guild.id].cleanup()
            del music_players[interaction.guild.id]

        # Disconnect from voice channel
        channel_name = interaction.guild.voice_client.channel.name
        await interaction.guild.voice_client.disconnect()
        
        await interaction.response.send_message(f"✅ Disconnected from {channel_name}")
        logger.info(f'Disconnected from voice channel: {channel_name} in guild: {interaction.guild.name}')

    except Exception as e:
        logger.error(f'Error in leave command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="music", description="Play music from YouTube")
async def music(interaction: discord.Interaction, link: str):
    """Play music from YouTube"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel. Use `/join` first.", ephemeral=True)
            return

        # Defer response as YouTube processing can take time
        await interaction.response.defer()

        # Get or create music player
        if interaction.guild.id not in music_players:
            music_players[interaction.guild.id] = MusicPlayer(interaction.guild.voice_client)

        player = music_players[interaction.guild.id]

        # Add to queue and play
        result = await player.add_to_queue(link)
        
        if result['success']:
            if result['position'] == 0:
                await interaction.followup.send(f"🎵 Now playing: **{result['title']}**")
            else:
                await interaction.followup.send(f"📝 Added to queue (position {result['position']}): **{result['title']}**")
        else:
            await interaction.followup.send(f"❌ Error: {result['error']}")

    except Exception as e:
        logger.error(f'Error in music command: {e}')
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")

@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    """Skip the current song"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

        # Get music player
        if interaction.guild.id not in music_players:
            await interaction.response.send_message("❌ No music player found.", ephemeral=True)
            return

        player = music_players[interaction.guild.id]
        
        if player.is_playing():
            player.skip()
            await interaction.response.send_message("⏭️ Skipped current song")
        else:
            await interaction.response.send_message("❌ No song is currently playing", ephemeral=True)

    except Exception as e:
        logger.error(f'Error in skip command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="stop", description="Stop music and clear queue")
async def stop(interaction: discord.Interaction):
    """Stop music and clear queue"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

        # Get music player
        if interaction.guild.id not in music_players:
            await interaction.response.send_message("❌ No music player found.", ephemeral=True)
            return

        player = music_players[interaction.guild.id]
        await player.stop()
        await interaction.response.send_message("⏹️ Stopped music and cleared queue")

    except Exception as e:
        logger.error(f'Error in stop command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="queue", description="Show the current music queue")
async def queue(interaction: discord.Interaction):
    """Show the current music queue"""
    try:
        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

        # Get music player
        if interaction.guild.id not in music_players:
            await interaction.response.send_message("❌ No music player found.", ephemeral=True)
            return

        player = music_players[interaction.guild.id]
        queue_info = player.get_queue()
        
        if not queue_info['queue'] and not queue_info['current']:
            await interaction.response.send_message("📝 Queue is empty")
            return

        embed = discord.Embed(title="🎵 Music Queue", color=0x00ff00)
        
        if queue_info['current']:
            embed.add_field(name="Now Playing", value=queue_info['current'], inline=False)
        
        if queue_info['queue']:
            queue_text = ""
            for i, song in enumerate(queue_info['queue'][:10], 1):  # Show first 10 songs
                queue_text += f"{i}. {song}\n"
            
            if len(queue_info['queue']) > 10:
                queue_text += f"... and {len(queue_info['queue']) - 10} more"
            
            embed.add_field(name="Up Next", value=queue_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        logger.error(f'Error in queue command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="mute", description="Server mute all users in the bot's voice channel")
async def mute(interaction: discord.Interaction):
    """Server mute all users in the bot's current voice channel"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

        # Defer response as muting operations can take time
        await interaction.response.defer()

        # Get the voice channel the bot is in
        voice_channel = interaction.guild.voice_client.channel
        
        # Get all members in the voice channel (excluding bots)
        members_to_mute = [member for member in voice_channel.members if not member.bot]
        
        if not members_to_mute:
            await interaction.followup.send("❌ No users to mute in the voice channel.")
            return

        # Mute all members
        muted_count = 0
        failed_mutes = []
        
        for member in members_to_mute:
            try:
                if not member.voice.mute:  # Only mute if not already muted
                    await member.edit(mute=True)
                    muted_count += 1
                    logger.info(f'Muted user: {member.name} in guild: {interaction.guild.name}')
            except discord.Forbidden:
                failed_mutes.append(member.name)
                logger.warning(f'Failed to mute user: {member.name} - insufficient permissions')
            except Exception as e:
                failed_mutes.append(member.name)
                logger.error(f'Error muting user {member.name}: {e}')

        # Send response
        if muted_count > 0:
            message = f"🔇 Successfully muted {muted_count} user(s) in {voice_channel.name}"
            if failed_mutes:
                message += f"\n⚠️ Failed to mute: {', '.join(failed_mutes)}"
            await interaction.followup.send(message)
        else:
            if failed_mutes:
                await interaction.followup.send(f"❌ Failed to mute any users. Check bot permissions.")
            else:
                await interaction.followup.send("ℹ️ All users in the voice channel are already muted.")

    except Exception as e:
        logger.error(f'Error in mute command: {e}')
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")

@bot.tree.command(name="unmute", description="Server unmute all users in the bot's voice channel")
async def unmute(interaction: discord.Interaction):
    """Server unmute all users in the bot's current voice channel"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        # Check if bot is in a voice channel
        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

        # Defer response as unmuting operations can take time
        await interaction.response.defer()

        # Get the voice channel the bot is in
        voice_channel = interaction.guild.voice_client.channel
        
        # Get all members in the voice channel (excluding bots)
        members_to_unmute = [member for member in voice_channel.members if not member.bot]
        
        if not members_to_unmute:
            await interaction.followup.send("❌ No users to unmute in the voice channel.")
            return

        # Unmute all members
        unmuted_count = 0
        failed_unmutes = []
        
        for member in members_to_unmute:
            try:
                if member.voice.mute:  # Only unmute if currently muted
                    await member.edit(mute=False)
                    unmuted_count += 1
                    logger.info(f'Unmuted user: {member.name} in guild: {interaction.guild.name}')
            except discord.Forbidden:
                failed_unmutes.append(member.name)
                logger.warning(f'Failed to unmute user: {member.name} - insufficient permissions')
            except Exception as e:
                failed_unmutes.append(member.name)
                logger.error(f'Error unmuting user {member.name}: {e}')

        # Send response
        if unmuted_count > 0:
            message = f"🔊 Successfully unmuted {unmuted_count} user(s) in {voice_channel.name}"
            if failed_unmutes:
                message += f"\n⚠️ Failed to unmute: {', '.join(failed_unmutes)}"
            await interaction.followup.send(message)
        else:
            if failed_unmutes:
                await interaction.followup.send(f"❌ Failed to unmute any users. Check bot permissions.")
            else:
                await interaction.followup.send("ℹ️ All users in the voice channel are already unmuted.")

    except Exception as e:
        logger.error(f'Error in unmute command: {e}')
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}")

@bot.tree.command(name="truth", description="Get an encouraging Bible verse")
async def truth(interaction: discord.Interaction):
    """Get a random encouraging Bible verse"""
    try:
        verse = random.choice(BIBLE_VERSES)
        embed = discord.Embed(
            title="Truth from God's Word",
            description=verse,
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
        logger.info(f'Truth command used by {interaction.user.name} in guild: {interaction.guild.name}')

    except Exception as e:
        logger.error(f'Error in truth command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="weather", description="Get current weather for a city")
async def weather(interaction: discord.Interaction, city: str):
    """Get current weather information for a specified city"""
    try:
        await interaction.response.defer()
        
        # OpenWeatherMap API (free tier)
        # Note: You'll need to get a free API key from openweathermap.org
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            await interaction.followup.send("❌ Weather service is not configured. Please ask the bot owner to set up the weather API key.")
            return
        
        async with aiohttp.ClientSession() as session:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract weather information
                    temp = data['main']['temp']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    description = data['weather'][0]['description'].title()
                    city_name = data['name']
                    country = data['sys']['country']
                    
                    # Create weather embed
                    embed = discord.Embed(
                        title=f"Weather in {city_name}, {country}",
                        color=0x87CEEB
                    )
                    embed.add_field(name="Temperature", value=f"{temp}°C", inline=True)
                    embed.add_field(name="Feels Like", value=f"{feels_like}°C", inline=True)
                    embed.add_field(name="Humidity", value=f"{humidity}%", inline=True)
                    embed.add_field(name="Description", value=description, inline=False)
                    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
                    
                    await interaction.followup.send(embed=embed)
                    logger.info(f'Weather command used by {interaction.user.name} for {city}')
                else:
                    await interaction.followup.send(f"❌ Could not find weather information for '{city}'. Please check the city name and try again.")
    
    except Exception as e:
        logger.error(f'Error in weather command: {e}')
        await interaction.followup.send(f"❌ An error occurred while fetching weather data: {str(e)}")

@bot.tree.command(name="joke", description="Get a random joke")
async def joke(interaction: discord.Interaction):
    """Get a random joke to lighten the mood"""
    try:
        joke_text = random.choice(JOKES)
        embed = discord.Embed(
            title="Random Joke",
            description=joke_text,
            color=0xFFD700
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f'Joke command used by {interaction.user.name} in guild: {interaction.guild.name}')
    
    except Exception as e:
        logger.error(f'Error in joke command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="fact", description="Get a random fun fact")
async def fact(interaction: discord.Interaction):
    """Get a random fun fact"""
    try:
        fact_text = random.choice(FUN_FACTS)
        embed = discord.Embed(
            title="Did You Know?",
            description=fact_text,
            color=0x9932CC
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f'Fact command used by {interaction.user.name} in guild: {interaction.guild.name}')
    
    except Exception as e:
        logger.error(f'Error in fact command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="roll", description="Roll dice (e.g., 1d6, 2d20)")
async def roll(interaction: discord.Interaction, dice: str = "1d6"):
    """Roll dice with specified format (e.g., 1d6, 2d20)"""
    try:
        # Parse dice format (e.g., "2d20" -> 2 dice with 20 sides each)
        if 'd' not in dice.lower():
            await interaction.response.send_message("❌ Invalid dice format. Use format like '1d6' or '2d20'.", ephemeral=True)
            return
        
        parts = dice.lower().split('d')
        if len(parts) != 2:
            await interaction.response.send_message("❌ Invalid dice format. Use format like '1d6' or '2d20'.", ephemeral=True)
            return
        
        try:
            num_dice = int(parts[0]) if parts[0] else 1
            num_sides = int(parts[1])
        except ValueError:
            await interaction.response.send_message("❌ Invalid dice format. Use format like '1d6' or '2d20'.", ephemeral=True)
            return
        
        # Validate input
        if num_dice < 1 or num_dice > 20:
            await interaction.response.send_message("❌ Number of dice must be between 1 and 20.", ephemeral=True)
            return
        
        if num_sides < 2 or num_sides > 100:
            await interaction.response.send_message("❌ Number of sides must be between 2 and 100.", ephemeral=True)
            return
        
        # Roll the dice
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(rolls)
        
        # Create result embed
        embed = discord.Embed(
            title=f"Rolling {num_dice}d{num_sides}",
            color=0xFF6347
        )
        
        if num_dice == 1:
            embed.add_field(name="Result", value=f"**{rolls[0]}**", inline=False)
        else:
            embed.add_field(name="Individual Rolls", value=f"{', '.join(map(str, rolls))}", inline=False)
            embed.add_field(name="Total", value=f"**{total}**", inline=False)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f'Roll command used by {interaction.user.name}: {dice} -> {rolls}')
    
    except Exception as e:
        logger.error(f'Error in roll command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="coinflip", description="Flip a coin")
async def coinflip(interaction: discord.Interaction):
    """Flip a coin and get heads or tails"""
    try:
        result = random.choice(["Heads", "Tails"])
        
        embed = discord.Embed(
            title="Coin Flip",
            description=f"**{result}**",
            color=0xFFD700
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f'Coinflip command used by {interaction.user.name}: {result}')
    
    except Exception as e:
        logger.error(f'Error in coinflip command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="pick", description="Pick a random choice from a list")
async def pick(interaction: discord.Interaction, choices: str):
    """Pick a random choice from a comma-separated list"""
    try:
        # Split choices by comma and clean them up
        choice_list = [choice.strip() for choice in choices.split(',') if choice.strip()]
        
        if len(choice_list) < 2:
            await interaction.response.send_message("❌ Please provide at least 2 choices separated by commas.", ephemeral=True)
            return
        
        if len(choice_list) > 20:
            await interaction.response.send_message("❌ Please provide no more than 20 choices.", ephemeral=True)
            return
        
        selected = random.choice(choice_list)
        
        embed = discord.Embed(
            title="Random Choice",
            description=f"I pick: **{selected}**",
            color=0x00CED1
        )
        embed.add_field(name="Choices", value=f"{', '.join(choice_list)}", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        logger.info(f'Pick command used by {interaction.user.name}: {selected} from {choice_list}')
    
    except Exception as e:
        logger.error(f'Error in pick command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="8ball", description="Ask the magic 8-ball a question")
async def eight_ball(interaction: discord.Interaction, question: str):
    """Ask the magic 8-ball a yes/no question"""
    try:
        if not question.strip():
            await interaction.response.send_message("❌ Please ask a question!", ephemeral=True)
            return
        
        response = random.choice(EIGHT_BALL_RESPONSES)
        
        embed = discord.Embed(
            title="Magic 8-Ball",
            color=0x4B0082
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f"**{response}**", inline=False)
        embed.set_footer(text=f"Asked by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'8ball command used by {interaction.user.name}: {question}')
    
    except Exception as e:
        logger.error(f'Error in 8ball command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="wouldyourather", description="Get a random 'would you rather' question")
async def would_you_rather(interaction: discord.Interaction):
    """Get a random 'would you rather' question"""
    try:
        question = random.choice(WOULD_YOU_RATHER)
        
        embed = discord.Embed(
            title="Would You Rather?",
            description=question,
            color=0xFF1493
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Would you rather command used by {interaction.user.name}')
    
    except Exception as e:
        logger.error(f'Error in would you rather command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="trivia", description="Answer a trivia question")
async def trivia(interaction: discord.Interaction):
    """Get a random trivia question"""
    try:
        question_data = random.choice(TRIVIA_QUESTIONS)
        question = question_data["question"]
        correct_answer = question_data["answer"]
        options = question_data["options"]
        
        # Create embed with multiple choice options
        embed = discord.Embed(
            title="Trivia Question",
            description=question,
            color=0x00FF7F
        )
        
        options_text = ""
        for i, option in enumerate(options, 1):
            options_text += f"{i}. {option}\n"
        
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.add_field(name="Answer", value=f"||{correct_answer}||", inline=False)
        embed.set_footer(text=f"Click the spoiler to reveal the answer | Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Trivia command used by {interaction.user.name}')
    
    except Exception as e:
        logger.error(f'Error in trivia command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="quote", description="Get an inspirational quote")
async def quote(interaction: discord.Interaction):
    """Get a random inspirational quote"""
    try:
        quote_text = random.choice(INSPIRATIONAL_QUOTES)
        
        embed = discord.Embed(
            title="Inspirational Quote",
            description=quote_text,
            color=0x20B2AA
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Quote command used by {interaction.user.name}')
    
    except Exception as e:
        logger.error(f'Error in quote command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="rps", description="Play Rock Paper Scissors with the bot")
async def rock_paper_scissors(interaction: discord.Interaction, choice: str):
    """Play Rock Paper Scissors with the bot"""
    try:
        valid_choices = ["rock", "paper", "scissors"]
        user_choice = choice.lower()
        
        if user_choice not in valid_choices:
            await interaction.response.send_message("❌ Please choose rock, paper, or scissors!", ephemeral=True)
            return
        
        bot_choice = random.choice(valid_choices)
        
        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie!"
            color = 0xFFFF00
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = 0x00FF00
        else:
            result = "I win!"
            color = 0xFF0000
        
        embed = discord.Embed(
            title="Rock Paper Scissors",
            color=color
        )
        embed.add_field(name="Your Choice", value=user_choice.capitalize(), inline=True)
        embed.add_field(name="My Choice", value=bot_choice.capitalize(), inline=True)
        embed.add_field(name="Result", value=f"**{result}**", inline=False)
        embed.set_footer(text=f"Played by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'RPS command used by {interaction.user.name}: {user_choice} vs {bot_choice}')
    
    except Exception as e:
        logger.error(f'Error in rps command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="serverstats", description="Show server statistics")
async def server_stats(interaction: discord.Interaction):
    """Show server statistics"""
    try:
        guild = interaction.guild
        
        # Count different types of channels
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Count members
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        
        # Count roles
        total_roles = len(guild.roles)
        
        # Server creation date
        created_at = guild.created_at.strftime("%B %d, %Y")
        
        embed = discord.Embed(
            title=f"Server Statistics for {guild.name}",
            color=0x7289DA
        )
        
        embed.add_field(name="Members", value=f"Total: {total_members}\nOnline: {online_members}", inline=True)
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}", inline=True)
        embed.add_field(name="Roles", value=str(total_roles), inline=True)
        embed.add_field(name="Created", value=created_at, inline=True)
        embed.add_field(name="Server ID", value=str(guild.id), inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Server stats command used by {interaction.user.name}')
    
    except Exception as e:
        logger.error(f'Error in server stats command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="avatar", description="Show someone's avatar")
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    """Show a user's avatar"""
    try:
        target_user = user or interaction.user
        
        embed = discord.Embed(
            title=f"{target_user.display_name}'s Avatar",
            color=0x00CED1
        )
        embed.set_image(url=target_user.display_avatar.url)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Avatar command used by {interaction.user.name} for {target_user.name}')
    
    except Exception as e:
        logger.error(f'Error in avatar command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="userinfo", description="Show information about a user")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    """Show information about a user"""
    try:
        target_user = user or interaction.user
        
        # Calculate account age
        account_created = target_user.created_at.strftime("%B %d, %Y")
        joined_server = target_user.joined_at.strftime("%B %d, %Y") if target_user.joined_at else "Unknown"
        
        # Get top role
        top_role = target_user.top_role.name if target_user.top_role != interaction.guild.default_role else "None"
        
        embed = discord.Embed(
            title=f"User Information for {target_user.display_name}",
            color=target_user.color
        )
        
        embed.add_field(name="Username", value=str(target_user), inline=True)
        embed.add_field(name="Nickname", value=target_user.display_name, inline=True)
        embed.add_field(name="User ID", value=str(target_user.id), inline=True)
        embed.add_field(name="Account Created", value=account_created, inline=True)
        embed.add_field(name="Joined Server", value=joined_server, inline=True)
        embed.add_field(name="Top Role", value=top_role, inline=True)
        embed.add_field(name="Status", value=str(target_user.status).title(), inline=True)
        embed.add_field(name="Bot", value="Yes" if target_user.bot else "No", inline=True)
        
        if target_user.display_avatar:
            embed.set_thumbnail(url=target_user.display_avatar.url)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Userinfo command used by {interaction.user.name} for {target_user.name}')
    
    except Exception as e:
        logger.error(f'Error in userinfo command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="poll", description="Create a simple poll")
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    """Create a poll with 2-4 options"""
    try:
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        
        embed = discord.Embed(
            title="Poll",
            description=question,
            color=0xFF69B4
        )
        
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        
        options_text = ""
        for i, option in enumerate(options):
            options_text += f"{reactions[i]} {option}\n"
        
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.set_footer(text=f"Poll created by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
        # Add reactions
        message = await interaction.original_response()
        for i in range(len(options)):
            await message.add_reaction(reactions[i])
        
        logger.info(f'Poll command used by {interaction.user.name}: {question}')
    
    except Exception as e:
        logger.error(f'Error in poll command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    """Show available commands"""
    try:
        embed = discord.Embed(
            title="Bot Commands",
            description="Here are the available commands:",
            color=0x00ff00
        )
        
        # Admin commands
        admin_commands = [
            "`/join <channel>` - Join a voice channel",
            "`/leave` - Leave the current voice channel",
            "`/music <link>` - Play music from YouTube",
            "`/skip` - Skip the current song",
            "`/stop` - Stop music and clear queue",
            "`/mute` - Server mute all users in bot's voice channel",
            "`/unmute` - Server unmute all users in bot's voice channel"
        ]
        
        # General commands
        general_commands = [
            "`/queue` - Show the current music queue",
            "`/truth` - Get an encouraging Bible verse",
            "`/help` - Show this help message"
        ]
        
        # Fun commands
        fun_commands = [
            "`/weather <city>` - Get current weather for a city",
            "`/joke` - Get a random joke",
            "`/fact` - Get a random fun fact",
            "`/roll <dice>` - Roll dice (e.g., 1d6, 2d20)",
            "`/coinflip` - Flip a coin",
            "`/pick <choices>` - Pick random choice from comma-separated list",
            "`/8ball <question>` - Ask the magic 8-ball a question",
            "`/wouldyourather` - Get a 'would you rather' question",
            "`/trivia` - Answer a trivia question",
            "`/quote` - Get an inspirational quote",
            "`/rps <choice>` - Play Rock Paper Scissors with the bot"
        ]
        
        # Social commands
        social_commands = [
            "`/serverstats` - Show server statistics",
            "`/avatar [user]` - Show someone's avatar",
            "`/userinfo [user]` - Show user information",
            "`/poll <question> <option1> <option2> [option3] [option4]` - Create a poll"
        ]
        
        embed.add_field(name="Admin Commands", value="\n".join(admin_commands), inline=False)
        embed.add_field(name="General Commands", value="\n".join(general_commands), inline=False)
        embed.add_field(name="Fun Commands", value="\n".join(fun_commands), inline=False)
        embed.add_field(name="Social Commands", value="\n".join(social_commands), inline=False)
        embed.add_field(name="Note", value="Admin commands require administrator permissions.", inline=False)
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Help command used by {interaction.user.name} in guild: {interaction.guild.name}')

    except Exception as e:
        logger.error(f'Error in help command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

# Error handling for commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    """Handle application command errors"""
    logger.error(f'Command error in {interaction.command.name if interaction.command else "unknown"}: {error}')
    
    if not interaction.response.is_done():
        await interaction.response.send_message(f"❌ An error occurred: {str(error)}", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ An error occurred: {str(error)}")

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.error(f'Failed to run bot: {e}')
