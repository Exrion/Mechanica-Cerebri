import discord
from discord.ext import commands

# Constants
description = '''A simple music bot by Exrion#0854. Find my commands at https://github.com/Exrion/Mechanica-Cerebri'''
command_prefix = '~'

def bot():
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True

    bot = commands.Bot(command_prefix=command_prefix,
                    description=description, intents=intents)
    return bot