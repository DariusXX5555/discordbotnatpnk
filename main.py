import discord
from discord.ext import commands
from discord import app_commands
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
    "I can do all things through Christ who strengthens me. - Philippians 4:13"
]

# Fun lists
JOKES = [
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the math book look sad? Because it had too many problems."
]
FUN_FACTS = [
    "Honey never spoils.",
    "A group of flamingos is called a 'flamboyance'.",
    "Bananas are berries, but strawberries are not."
]
WOULD_YOU_RATHER = [
    "Would you rather be able to fly or be invisible?",
    "Would you rather never have to sleep or never have to eat?",
    "Would you rather have the ability to time travel or teleport?"
]
INSPIRATIONAL_QUOTES = [
    "The best way to get started is to quit talking and begin doing. – Walt Disney",
    "Don’t let yesterday take up too much of today. – Will Rogers",
    "It’s not whether you get knocked down, it’s whether you get up. – Vince Lombardi"
]

# --- Choices for commands ---
RPS_CHOICES = [
    app_commands.Choice(name="Rock", value="rock"),
    app_commands.Choice(name="Paper", value="paper"),
    app_commands.Choice(name="Scissors", value="scissors"),
]
EXCLUDE_ACTIONS = [
    app_commands.Choice(name="Add (exclude a user)", value="add"),
    app_commands.Choice(name="Remove (include a user)", value="remove"),
    app_commands.Choice(name="List (show excluded)", value="list"),
    app_commands.Choice(name="Clear (remove all excluded)", value="clear"),
]

# Excluded users per guild for mute/unmute
excluded_users = {}

# --------- Bot Events ---------
@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} ({bot.user.id})')
    try:
        synced = await bot.tree.sync()
        logger.info(f'Successfully synced {len(synced)} application commands')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

@bot.event
async def on_guild_remove(guild):
    """Called when bot leaves a guild"""
    logger.info(f'Left guild: {guild.name} ({guild.id})')
    # Cleanup music player
    if guild.id in music_players:
        await music_players[guild.id].cleanup()
        del music_players[guild.id]

# --------- Voice/Music Commands ---------
@bot.tree.command(name="join", description="Join a voice channel (by name or mention)")
@app_commands.describe(channel="Voice channel name or mention")
async def join(interaction: discord.Interaction, channel: str):
    """Join a voice channel by name or mention"""
    try:
        # Check if user is admin
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        await interaction.response.defer()

        # Try to resolve channel mention
        voice_channel = None
        if channel.startswith("<#") and channel.endswith(">"):
            try:
                channel_id = int(channel[2:-1])
                for ch in interaction.guild.voice_channels:
                    if ch.id == channel_id:
                        voice_channel = ch
                        break
            except ValueError:
                pass
        if not voice_channel:
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
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

        if interaction.guild.id in music_players:
            await music_players[interaction.guild.id].cleanup()
            del music_players[interaction.guild.id]

        channel_name = interaction.guild.voice_client.channel.name
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message(f"✅ Disconnected from {channel_name}")
        logger.info(f'Disconnected from voice channel: {channel_name} in guild: {interaction.guild.name}')

    except Exception as e:
        logger.error(f'Error in leave command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="music", description="Play music from YouTube")
@app_commands.describe(link="YouTube link or search term")
async def music(interaction: discord.Interaction, link: str):
    """Play music from YouTube"""
    try:
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel. Use `/join` first.", ephemeral=True)
            return

        await interaction.response.defer()

        if interaction.guild.id not in music_players:
            music_players[interaction.guild.id] = MusicPlayer(interaction.guild.voice_client)

        player = music_players[interaction.guild.id]
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
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

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
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        if not interaction.guild.voice_client:
            await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
            return

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
        if interaction.guild.id not in music_players:
            await interaction.response.send_message("❌ No music player found.", ephemeral=True)
            return
        queue = music_players[interaction.guild.id].get_queue()
        if not queue:
            await interaction.response.send_message("🎵 The queue is empty.", ephemeral=True)
            return
        description = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(queue)])
        embed = discord.Embed(title="Music Queue", description=description, color=0x3498db)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f'Error in queue command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

# --------- Fun Commands ---------
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
@app_commands.describe(dice="Dice format (e.g. 1d6 for 1 six-sided die, 2d20 for two 20-sided dice)")
async def roll(interaction: discord.Interaction, dice: str = "1d6"):
    """Roll dice with specified format (e.g., 1d6, 2d20)"""
    try:
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
        if num_dice < 1 or num_dice > 20:
            await interaction.response.send_message("❌ Number of dice must be between 1 and 20.", ephemeral=True)
            return
        if num_sides < 2 or num_sides > 100:
            await interaction.response.send_message("❌ Number of sides must be between 2 and 100.", ephemeral=True)
            return
        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(rolls)
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

@bot.tree.command(name="pick", description="Pick a random choice from a list (comma-separated)")
@app_commands.describe(choices="Type options separated by commas, e.g., apple, banana, orange")
async def pick(interaction: discord.Interaction, choices: str):
    """Pick a random choice from a comma-separated list"""
    try:
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

@bot.tree.command(name="rps", description="Play Rock Paper Scissors with the bot")
@app_commands.describe(choice="Pick your move!")
@app_commands.choices(choice=RPS_CHOICES)
async def rps(interaction: discord.Interaction, choice: app_commands.Choice[str]):
    """Play Rock Paper Scissors with the bot"""
    try:
        user_choice = choice.value
        valid_choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(valid_choices)
        if user_choice == bot_choice:
            result = "It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
        else:
            result = "You lose!"
        embed = discord.Embed(
            title="Rock Paper Scissors",
            description=f"You chose **{user_choice.title()}**\nBot chose **{bot_choice.title()}**\n\n**{result}**",
            color=0x1abc9c
        )
        await interaction.response.send_message(embed=embed)
        logger.info(f'RPS command: {interaction.user.name} ({user_choice}) vs Bot ({bot_choice}) - {result}')

    except Exception as e:
        logger.error(f'Error in rps command: {e}')
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

# --------- Utility, Info & Social Commands ---------
@bot.tree.command(name="weather", description="Get current weather for a city")
@app_commands.describe(city="City to get the weather for")
async def weather(interaction: discord.Interaction, city: str):
    """Get current weather information for a specified city"""
    try:
        await interaction.response.defer()
        api_key = os.getenv("OPENWEATHER_API_KEY", None)
        if not api_key:
            await interaction.followup.send("❌ Weather API key not set.")
            return
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Could not fetch weather info. Please check the city name.")
                    return
                data = await resp.json()
        desc = data["weather"][0]["description"].title()
        temp = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        embed = discord.Embed(
            title=f"Weather in {city.title()}",
            description=f"{desc}\nTemperature: {temp}°C (feels like {feels}°C)",
            color=0x1e90ff
        )
        await interaction.followup.send(embed=embed)
        logger.info(f'Weather command used by {interaction.user.name} for {city}')
    except Exception as e:
        logger.error(f'Error in weather command: {e}')
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

@bot.tree.command(name="avatar", description="Show someone's avatar")
@app_commands.describe(user="User to show avatar for (optional)")
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
@app_commands.describe(user="User to get info for (optional)")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    """Show information about a user"""
    try:
        target_user = user or interaction.user
        account_created = target_user.created_at.strftime("%B %d, %Y")
        joined_server = target_user.joined_at.strftime("%B %d, %Y") if target_user.joined_at else "Unknown"
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

@bot.tree.command(name="serverstats", description="Show server statistics")
async def server_stats(interaction: discord.Interaction):
    """Show server statistics"""
    try:
        guild = interaction.guild
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        total_roles = len(guild.roles)
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

# --------- Poll/Exclude/Help ---------
@bot.tree.command(name="poll", description="Create a simple poll")
@app_commands.describe(
    question="What are you polling about?",
    option1="First poll option",
    option2="Second poll option",
    option3="(Optional) Third poll option",
    option4="(Optional) Fourth poll option"
)
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    """Create a poll with 2-4 options"""
    try:
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        if len(options) < 2:
            await interaction.response.send_message("❌ Please provide at least two options.", ephemeral=True)
            return
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
        message = await interaction.original_response()
        for i in range(len(options)):
            await message.add_reaction(reactions[i])
        logger.info(f'Poll command used by {interaction.user.name}: {question}')
    except Exception as e:
        logger.error(f'Error in poll command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="exclude", description="Manage users excluded from mute/unmute commands")
@app_commands.describe(
    action="Pick what to do: add/remove/list/clear",
    user="User to add/remove (not needed for list/clear)"
)
@app_commands.choices(action=EXCLUDE_ACTIONS)
async def exclude(interaction: discord.Interaction, action: app_commands.Choice[str], user: discord.Member = None):
    """Manage users excluded from mute/unmute commands"""
    try:
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        if guild_id not in excluded_users:
            excluded_users[guild_id] = set()
        guild_excluded = excluded_users[guild_id]
        action_val = action.value

        if action_val == "add":
            if not user:
                await interaction.response.send_message("❌ Please specify a user to add to the exclusion list.", ephemeral=True)
                return
            if user.id in guild_excluded:
                await interaction.response.send_message(f"❌ {user.display_name} is already excluded from mute/unmute commands.", ephemeral=True)
                return
            guild_excluded.add(user.id)
            embed = discord.Embed(
                title="✅ User Added to Exclusion List",
                description=f"{user.display_name} has been added to the exclusion list and will not be affected by mute/unmute commands.",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
            logger.info(f'User {user.name} added to exclusion list by {interaction.user.name} in guild: {interaction.guild.name}')
        elif action_val == "remove":
            if not user:
                await interaction.response.send_message("❌ Please specify a user to remove from the exclusion list.", ephemeral=True)
                return
            if user.id not in guild_excluded:
                await interaction.response.send_message(f"❌ {user.display_name} is not in the exclusion list.", ephemeral=True)
                return
            guild_excluded.remove(user.id)
            embed = discord.Embed(
                title="✅ User Removed from Exclusion List",
                description=f"{user.display_name} has been removed from the exclusion list and will now be affected by mute/unmute commands.",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
            logger.info(f'User {user.name} removed from exclusion list by {interaction.user.name} in guild: {interaction.guild.name}')
        elif action_val == "list":
            if not guild_excluded:
                await interaction.response.send_message("📋 No users are currently excluded from mute/unmute commands.", ephemeral=True)
                return
            excluded_names = []
            for user_id in guild_excluded:
                member = interaction.guild.get_member(user_id)
                if member:
                    excluded_names.append(member.display_name)
                else:
                    excluded_names.append(f"Unknown User (ID: {user_id})")
            embed = discord.Embed(
                title="🛡️ Excluded Users",
                description="The following users are excluded from mute/unmute commands:",
                color=0x4169E1
            )
            embed.add_field(name="Excluded Users", value="\n".join(excluded_names), inline=False)
            embed.set_footer(text=f"Total excluded users: {len(excluded_names)}")
            await interaction.response.send_message(embed=embed)
            logger.info(f'Exclusion list viewed by {interaction.user.name} in guild: {interaction.guild.name}')
        elif action_val == "clear":
            if not guild_excluded:
                await interaction.response.send_message("❌ No users are currently excluded.", ephemeral=True)
                return
            excluded_count = len(guild_excluded)
            guild_excluded.clear()
            embed = discord.Embed(
                title="✅ Exclusion List Cleared",
                description=f"All {excluded_count} users have been removed from the exclusion list.",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
            logger.info(f'Exclusion list cleared by {interaction.user.name} in guild: {interaction.guild.name}')
        else:
            await interaction.response.send_message("❌ Invalid action. Use: `add`, `remove`, `list`, or `clear`", ephemeral=True)

    except Exception as e:
        logger.error(f'Error in exclude command: {e}')
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
        admin_commands = [
            "`/join <channel>` - Join a voice channel",
            "`/leave` - Leave the current voice channel",
            "`/music <link>` - Play music from YouTube",
            "`/skip` - Skip the current song",
            "`/stop` - Stop music and clear queue",
            "`/mute` - Server mute all users in bot's voice channel",
            "`/unmute` - Server unmute all users in bot's voice channel",
            "`/exclude <action> [user]` - Manage excluded users (add/remove/list/clear)"
        ]
        general_commands = [
            "`/queue` - Show the current music queue",
            "`/truth` - Get an encouraging Bible verse",
            "`/help` - Show this help message"
        ]
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

# --------- Error Handling ---------
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    """Handle application command errors"""
    logger.error(f'Command error in {interaction.command.name if interaction.command else "unknown"}: {error}')
    if not interaction.response.is_done():
        await interaction.response.send_message(f"❌ An error occurred: {str(error)}", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ An error occurred: {str(error)}")

# --------- Bot Run ---------
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
