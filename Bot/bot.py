import discord
from discord.ext import commands

# Constants
description = '''Personal Discord Bot Testing'''
command_prefix = '~'

def bot():
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = commands.Bot(command_prefix=command_prefix,
                    description=description, intents=intents)
    return bot