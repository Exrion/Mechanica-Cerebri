import discord
from discord.ext import commands

# Constants
description = '''Personal Discord Bot Testing'''

def bot():
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = commands.Bot(command_prefix='#',
                    description=description, intents=intents)
    return bot