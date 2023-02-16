import asyncio
import itertools
import discord
from discord.ext import commands
import random
import sys

# Constants
ERROR_MISSINGARG = 'Command is missing argument(s) - {argument}'

# Configure sys.path
sys.path.append(r'./Bot')
sys.path.append(r'./PlayerUtility')
print('System Paths Loaded:\n', sys.path)

# Enviromental Variables
from envvars import load_var_token
DISCORDBOT_TOKEN = load_var_token()

# Setup Bot
from bot import bot
bot = bot()

# Init
from PlayerUtility import Player, YTDLSource
_Player = Player.Player
_YTDLSource = YTDLSource.YTDLSource
players = {}

# Setup Bot Commands
# On Ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# Simple Ping Pong
@bot.command(name='ping')
async def ping(ctx):
    """Ping Pong!"""
    embed = discord.Embed(title="", description='Pong!', color=discord.Color.green())
    await ctx.send(embed=embed)


# Utility Commands
# Date Joined
@bot.command(name='joined')
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    embed = discord.Embed(title="", description=f'{member.name} joined {discord.utils.format_dt(member.joined_at)}', color=discord.Color.green())
    await ctx.send(embed=embed)
    
@joined.error
async def joined_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="", description="Error: Guild Member not found!", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="", description=ERROR_MISSINGARG.format(argument='Guid Member'), color=discord.Color.red())
        await ctx.send(embed=embed)

# Coin Flip
@bot.command(name='coinflip')
async def coin_flip(ctx):
    """Heads of Tails Coin Flip"""
    flip = random.randint(0, 1)
    embed = discord.Embed(title="", description=('Heads' if flip == 0 else 'Tails'), color=discord.Color.green())
    await ctx.send(embed=embed)

# Choose
@bot.command(name='choose')
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    embed = discord.Embed(title="", description=random.choice(choices), color=discord.Color.green())
    await ctx.send(embed=embed)
@choose.error
async def choose_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="", description="Error: Disallowed input type", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="", description=ERROR_MISSINGARG.format(argument='Choices(string)'), color=discord.Color.red())
        await ctx.send(embed=embed)

# Subcommand Checker
@bot.group()
async def cool(ctx):
    """Says if a user is cool.
    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} is not cool')

@cool.command(name='bot')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, the bot is cool.')


# Main Commands
# Join Voice Channel
@bot.command(name='join')
async def joinVC(ctx):
    """Joins a voice channel"""
    channel = None

    if not channel:
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="", description="Error: User must be in a voice channel", color=discord.Color.red())
            await ctx.send(embed=embed)
            raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

    voice_channel = ctx.voice_client

    if voice_channel:
        if voice_channel.channel.id == channel.id:
            embed = discord.Embed(title="", description="Notice: Bot already connected to channel", color=discord.Color.blue())
            await ctx.send(embed=embed)
            return
        try:
            await voice_channel.move_to(channel)
        except asyncio.TimeoutError:
            raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
    else:
        try:
            await channel.connect(self_deaf=True)
        except asyncio.TimeoutError:
            raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        embed = discord.Embed(title="", description=f'Notice: Joining Channel - `{channel}`', color=discord.Color.blue())
        await ctx.send(embed=embed)

# Leave Voice Channel
@bot.command(name='leave')
async def leaveVC(ctx):
    """Leaves a voice channel"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Error: Currently not connected to a voice channel", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        cleanup(ctx)
        await ctx.send('Disconnected from voice channel')

# Instantiate Player
def get_player(ctx):
    """Retrieve the guild player, or generate one."""
    try:
        player = players[ctx.guild.id]
    except KeyError:
        player = _Player(ctx)
        players[ctx.guild.id] = player

    return player

# Cleanup after disconnect
async def cleanup(ctx):
    try:
        await ctx.guild.voice_client.disconnect()
    except AttributeError:
        pass

    try:
        del players[ctx.guild.id]
    except KeyError:
        pass

# Add Item to Queue
@bot.command(name='play', aliases=['p'])
async def addSong(ctx, search: str):
    """Adds song to queue and plays it."""
    voice_channel = ctx.voice_client
    if not voice_channel:
        await joinVC(ctx)
    
    player = get_player(ctx)
    source = await _YTDLSource.create_source(ctx, search, loop=None, download=False)
    await player.queue.put(source)
@addSong.error
async def addSong_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(title="", description="Error: Disallowed input type", color=discord.Color.red())
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(title="", description=ERROR_MISSINGARG.format(argument='Search Parameters(string | url)'), color=discord.Color.red())
        await ctx.send(embed=embed)

# Pause Playback
@bot.command(name='pause')
async def pauseSong(ctx):
    """Pauses Playback"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_playing():
        embed = discord.Embed(title="", description="Notice: Not currently playing anything", color=discord.Color.blue())
        return await ctx.send(embed=embed)
    elif voice_channel.is_paused():
        return

    voice_channel.pause()
    embed = discord.Embed(title="", description="Notice: Paused Playback", color=discord.Color.blue())
    return await ctx.send(embed=embed)

# Resume Playback
@bot.command(name='resume')
async def resumeSong(ctx):
    """Resumes Playback"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
        return await ctx.send(embed=embed)
    elif not voice_channel.is_paused():
        return

    voice_channel.resume()
    embed = discord.Embed(title="", description="Notice: Resumed Playback", color=discord.Color.blue())
    return await ctx.send(embed=embed)

# Skips Song
@bot.command(name='skip')
async def skipSong(ctx):
    """Skips current song"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
        return await ctx.send(embed=embed)
    
    if voice_channel.is_paused():
        pass
    elif not voice_channel.is_playing():
        return

    voice_channel.stop()

# Removes Song 
@bot.command(name='remove', aliases=['rm'])
async def removeSong(ctx, pos: int=None):
    """Removes Song from queue"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
        return await ctx.send(embed=embed)

    player = get_player(ctx)
    if pos == None:
        player.queue._queue.pop()
    else:
        try:
            song = player.queue._queue[pos-1]
            del player.queue._queue[pos-1]
            embed = discord.Embed(title="", description=f"Removed [{song['title']}]({song['webpage_url']}) [{song['requester'].mention}]", color=discord.Color.blue())
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(title="", description=f"Error: Could not find song at position `{pos}`", color=discord.Color.red())
            await ctx.send(embed=embed)

# Clear Queue
@bot.command(name='clear', aliases=['cl', 'clr', 'cr'])
async def clearQueue(ctx):
    """Clears queue of songs"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
        return await ctx.send(embed=embed)
    
    player = get_player(ctx)
    player.queue._queue.clear()
    embed = discord.Embed(title="", description="Notice: Queue has been cleared", color=discord.Color.blue())
    await ctx.send(embed=embed)

# Display Queue
@bot.command(name='queue', aliases=['q'])
async def displayQueue(ctx):
    """Display song queue"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
        return await ctx.send(embed=embed)
    
    player = get_player(ctx)
    if player.queue.empty():
        embed = discord.Embed(title="", description="Notice: Queue is empty", color=discord.Color.blue())
        await ctx.send(embed=embed)

    seconds = voice_channel.source.duration % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if hour > 0:
        duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
    else:
        duration = "%02dm %02ds" % (minutes, seconds)
    
    # Retrieve songs in queue
    upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
    format = '\n'.join(f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['webpage_url']}) | ` {duration} Requested by: {_['requester']}`\n" for _ in upcoming)
    format = f"\n__Now Playing__:\n[{voice_channel.source.title}]({voice_channel.source.web_url}) | ` {duration} Requested by: {voice_channel.source.requester}`\n\n__Up Next:__\n" + format + f"\n**{len(upcoming)} songs in queue**"
    embed = discord.Embed(title=f"Queue for {ctx.guild.name}", description=format, color=discord.Color.blue())
    embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

# Now Playing
@bot.command(name='np', aliases=['current', 'song', 'currentsong', 'playing'])
async def currentSong(ctx):
    """Display current song"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
        return await ctx.send(embed=embed)

    player = get_player(ctx)
    if not player.current:
        embed = discord.Embed(title="", description="Notice: Currently not playing anything", color=discord.Color.blue())
        return await ctx.send(embed=embed)

    seconds = voice_channel.source.duration % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if hour > 0:
        duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
    else:
        duration = "%02dm %02ds" % (minutes, seconds)

    embed = discord.Embed(title="", description=f"[{voice_channel.source.title}]({voice_channel.source.web_url}) [{voice_channel.source.requester.mention}] | `{duration}`", color=discord.Color.green())
    embed.set_author(icon_url=bot.user.avatar_url, name=f"Now Playing 🎶")
    await ctx.send(embed=embed)


# Run Bot
bot.run(DISCORDBOT_TOKEN)