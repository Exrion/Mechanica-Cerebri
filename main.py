import asyncio
import discord
from discord.ext import commands
import random
import sys

# Constants
ERROR_MISSINGARG = 'Command is missing argument(s) - {argument}'

# Configure sys.path
sys.path.append(r'./Bot')
print('System Paths Loaded:\n', sys.path)

# Enviromental Variables
from envvars import load_var_token
DISCORDBOT_TOKEN = load_var_token()

# Setup Bot
from bot import bot
bot = bot()

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
    await ctx.send(f'Joined `{channel}`')

# Leave Voice Channel
@bot.command(name='leave')
async def leaveVC(ctx):
    """Leaves a voice channel"""
    voice_channel = ctx.voice_client

    if not voice_channel or not voice_channel.is_connected():
        embed = discord.Embed(title="", description="Error: Currently not connected to a voice channel", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        await voice_channel.disconnect()
        await ctx.send('Disconnected from voice channel')

# Run Bot
bot.run(DISCORDBOT_TOKEN)