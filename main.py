import discord
from discord.ext import commands
import random
import sys

# Constants
ERROR_MISSINGARG = 'Command is missing argument(s) - {argument}'

# Configure sys.path
sys.path.append(r'./Commands')
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
    await ctx.send('Pong!')


# Utility Commands
# Date Joined
@bot.command(name='joined')
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')
@joined.error
async def joined_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Guild Member not found!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(ERROR_MISSINGARG.format(argument='Guid Member'))

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
# Coin Flip
@bot.command(name='coinflip')
async def coin_flip(ctx):
    """Heads of Tails Coin Flip"""
    flip = random.randint(0, 1)
    await ctx.send('Heads' if flip == 0 else 'Tails')

@bot.command(name='choose')
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))
@choose.error
async def choose_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Error: Disallowed input type')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(ERROR_MISSINGARG.format(argument='Choices(string)'))

# Run Bot
bot.run(DISCORDBOT_TOKEN)