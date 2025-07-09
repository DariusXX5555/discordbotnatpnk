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
    if guild.id in music_players:
        await music_players[guild.id].cleanup()
        del music_players[guild.id]

@bot.tree.command(name="join", description="Join a voice channel")
async def join(interaction: discord.Interaction, channel: str):
    """Join a voice channel"""
    try:
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        await interaction.response.defer()
        voice_channel = discord.utils.get(interaction.guild.voice_channels, name=channel)
        if not voice_channel:
            await interaction.followup.send(f"❌ Voice channel '{channel}' not found.")
            return
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel.id == voice_channel.id:
                await interaction.followup.send(f"✅ Already connected to {voice_channel.name}")
                return
            else:
                await interaction.guild.voice_client.disconnect()
        voice_client = await voice_channel.connect(timeout=60.0, reconnect=True)
        logger.info(f'Connected to voice channel: {voice_channel.name} in guild: {interaction.guild.name}')
        music_players[interaction.guild.id] = music_players.get(interaction.guild.id, MusicPlayer(voice_client))
        music_players[interaction.guild.id].voice_client = voice_client
        await interaction.followup.send(f"✅ Connected to {voice_channel.name}")
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ Connection timed out."
                                    " This may be due to network restrictions. The bot works best self-hosted or on a VPS.")
        logger.error(f'Connection timeout for voice channel: {channel}')
    except Exception as e:
        logger.error(f'Error in join command: {e}')
        await interaction.followup.send(f"❌ Failed to connect: {e}")

@bot.tree.command(name="leave", description="Leave the current voice channel")
async def leave(interaction: discord.Interaction):
    """Leave the current voice channel"""
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
        return
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("❌ Bot is not connected to a voice channel.", ephemeral=True)
        return
    if interaction.guild.id in music_players:
        await music_players[interaction.guild.id].cleanup()
        del music_players[interaction.guild.id]
    channel_name = vc.channel.name
    await vc.disconnect()
    await interaction.response.send_message(f"✅ Disconnected from {channel_name}")
    logger.info(f'Disconnected from voice channel: {channel_name}')

@bot.tree.command(name="music", description="Play music from YouTube")
async def music(interaction: discord.Interaction, link: str):
    """Play music from YouTube"""
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
        return
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("❌ Bot is not connected to a voice channel. Use `/join` first.", ephemeral=True)
        return
    await interaction.response.defer()
    player = music_players.setdefault(interaction.guild.id, MusicPlayer(vc))
    player.voice_client = vc
    result = await player.add_to_queue(link)
    if result['success']:
        msg = (f"🎵 Now playing: **{result['title']}**" if result['position']==0
               else f"📝 Added to queue (position {result['position']}): **{result['title']}**")
        await interaction.followup.send(msg)
    else:
        await interaction.followup.send(f"❌ Error: {result['error']}")

@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    """Skip the current song"""
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
        return
    vc = interaction.guild.voice_client
    if not vc or interaction.guild.id not in music_players:
        await interaction.response.send_message("❌ No music player found.", ephemeral=True)
        return
    player = music_players[interaction.guild.id]
    if player.is_playing():
        player.skip()
        await interaction.response.send_message("⏭️ Skipped current song")
    else:
        await interaction.response.send_message("❌ No song is currently playing", ephemeral=True)

@bot.tree.command(name="queue", description="Show the current music queue")
async def queue(interaction: discord.Interaction):
    """Show the current music queue"""
    vc = interaction.guild.voice_client
    if not vc or interaction.guild.id not in music_players:
        await interaction.response.send_message("❌ Bot is not connected or no music player.", ephemeral=True)
        return
    queue_info = music_players[interaction.guild.id].get_queue_info()
    if not queue_info:
        await interaction.response.send_message("📝 Queue is empty", ephemeral=True)
        return
    embed = discord.Embed(title="🎵 Music Queue", color=0x3498db)
    if queue_info['current']:
        embed.add_field(name="Now Playing", value=f"**{queue_info['current']}**", inline=False)
    if queue_info['upcoming']:
        upcoming_list = [f"{i}. {song}" for i,song in enumerate(queue_info['upcoming'][:10],1)]
        embed.add_field(name="Up Next", value="\n".join(upcoming_list), inline=False)
        if len(queue_info['upcoming'])>10:
            embed.add_field(name="", value=f"... and {len(queue_info['upcoming'])-10} more songs", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="songs", description="List available music in the bot's library")
async def songs(interaction: discord.Interaction):
    """List available local music files"""
    if not is_admin(interaction.user):
        await interaction.response.send_message(embed=create_error_embed("Access Denied",
            "Only administrators can use this command."), ephemeral=True)
        return
    from music_library import MusicLibrary
    library = MusicLibrary()
    available_songs = music_players.get(interaction.guild.id, library).get_available_songs()
    if not available_songs:
        embed = create_info_embed("Music Library",
            "No songs available. Add files to music folder and use `/music [name]`.")
    else:
        listing = "\n".join(f"• {s}" for s in available_songs[:20]) +
                  (f"\n... and {len(available_songs)-20} more" if len(available_songs)>20 else "")
        embed = create_info_embed(f"Available Songs ({len(available_songs)})", listing+"\nUsage: /music [song name]")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="truth", description="Discover wisdom and encouragement")
async def truth(interaction: discord.Interaction):
    """Get a random Bible verse"""
    try:
        verse = random.choice(BIBLE_VERSES)
        embed = discord.Embed(title="✝️ Truth from God's Word", description=f"*{verse}*", color=0xffd700)
        embed.set_footer(text="May this verse bless and encourage you today!")
        await interaction.response.send_message(embed=embed)
        logger.info(f'Sent Bible verse to user: {interaction.user.name}')
    except Exception as e:
        logger.error(f'Error in truth command: {e}')
        await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

# New commands: mute_all & unmute_all
@bot.tree.command(name="mute_all", description="Server-mute everyone in my current voice channel")
async def mute_all(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
    vc = interaction.guild.voice_client
    if not vc or not vc.channel:
        return await interaction.response.send_message("❌ I'm not in a voice channel.", ephemeral=True)
    await interaction.response.defer(thinking=True)
    failed=[]
    for m in vc.channel.members:
        if m==bot.user: continue
        try: await m.edit(mute=True)
        except: failed.append(m.name)
    msg = f"🔇 All users in **{vc.channel.name}** have been server-muted." if not failed else f"🔇 Muted everyone but failed on: {', '.join(failed)}"
    await interaction.followup.send(msg, ephemeral=bool(failed))

@bot.tree.command(name="unmute_all", description="Server-unmute everyone in my current voice channel")
async def unmute_all(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        return await interaction.response.send_message("❌ You need administrator permissions.", ephemeral=True)
    vc = interaction.guild.voice_client
    if not vc or not vc.channel:
        return await interaction.response.send_message("❌ I'm not in a voice channel.", ephemeral=True)
    await interaction.response.defer(thinking=True)
    failed=[]
    for m in vc.channel.members:
        if m==bot.user: continue
        try: await m.edit(mute=False)
        except: failed.append(m.name)
    msg = f"🔊 All users in **{vc.channel.name}** have been server-unmuted." if not failed else f"🔊 Unmuted everyone but failed on: {', '.join(failed)}"
    await interaction.followup.send(msg, ephemeral=bool(failed))

@bot.event
async def on_voice_state_update(member, before, after):
    """Handle voice state updates"""
    if member==bot.user and before.channel and not after.channel:
        gid=before.channel.guild.id
        if gid in music_players:
            await music_players[gid].cleanup()
            del music_players[gid]
        logger.info(f'Bot disconnected from voice channel in guild: {before.channel.guild.name}')


def main():
    try:
        bot.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        logger.error("Invalid bot token provided")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
