import discord
from discord.ext import commands
import asyncio
import logging
import os
import random
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
            title="🙏 Truth from God's Word",
            description=verse,
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
        logger.info(f'Truth command used by {interaction.user.name} in guild: {interaction.guild.name}')

    except Exception as e:
        logger.error(f'Error in truth command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="help", description="Show available commands")
async def help_command(interaction: discord.Interaction):
    """Show available commands"""
    try:
        embed = discord.Embed(
            title="🤖 Bot Commands",
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
        
        embed.add_field(name="🛡️ Admin Commands", value="\n".join(admin_commands), inline=False)
        embed.add_field(name="📖 General Commands", value="\n".join(general_commands), inline=False)
        embed.add_field(name="ℹ️ Note", value="Admin commands require administrator permissions.", inline=False)
        
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
