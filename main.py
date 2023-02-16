import asyncio
import os
import discord
from discord.ext import commands
import sys

# Constants
ERROR_MISSINGARG = 'Command is missing argument(s) - {argument}'

# Configure sys.path
sys.path.append(r'./Bot')
sys.path.append(r'./PlayerUtility')
sys.path.append(r'./cogs')
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

# On Ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# Run Bot
def main():
    from cogs.MainBot import MainBot

    bot.add_cog(MainBot(bot))
    bot.run(DISCORDBOT_TOKEN)

asyncio.run(main())