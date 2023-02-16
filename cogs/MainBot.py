import asyncio
import itertools
import traceback
import discord
from discord.ext import commands
import random
import sys

class MainBot(commands.Cog):
    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    # Utility Commands
    # Simple Ping Pong
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Ping Pong!"""
        embed = discord.Embed(title="", description='Pong!', color=discord.Color.green())
        await ctx.send(embed=embed)

    # Date Joined
    @commands.command(name='joined')
    async def joined(self, ctx, member: discord.Member):
        """Says when a member joined."""
        embed = discord.Embed(title="", description=f'{member.name} joined {discord.utils.format_dt(member.joined_at)}', color=discord.Color.green())
        await ctx.send(embed=embed)
        
    @joined.error
    async def joined_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="", description="Error: Guild Member not found!", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="", description=ERROR_MISSINGARG.format(argument='Guid Member'), color=discord.Color.red())
            await ctx.send(embed=embed)

    # Coin Flip
    @commands.command(name='coinflip')
    async def coin_flip(self, ctx):
        """Heads of Tails Coin Flip"""
        flip = random.randint(0, 1)
        embed = discord.Embed(title="", description=('Heads' if flip == 0 else 'Tails'), color=discord.Color.green())
        await ctx.send(embed=embed)

    # Choose
    @commands.command(name='choose')
    async def choose(self, ctx, *choices: str):
        """Chooses between multiple choices."""
        embed = discord.Embed(title="", description=random.choice(choices), color=discord.Color.green())
        await ctx.send(embed=embed)
    @choose.error
    async def choose_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="", description="Error: Disallowed input type", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="", description=ERROR_MISSINGARG.format(argument='Choices(string)'), color=discord.Color.red())
            await ctx.send(embed=embed)

    # Subcommand Checker
    @commands.group()
    async def cool(self, ctx):
        """Says if a user is cool.
        In reality this just checks if a subcommand is being invoked.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(f'No, {ctx.subcommand_passed} is not cool')

    @cool.command(name='bot')
    async def _bot(self, ctx):
        """Is the bot cool?"""
        await ctx.send('Yes, the bot is cool.')

    # Main Commands
    # Join Voice Channel
    @commands.command(name='join')
    async def joinVC(self, ctx):
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
    @commands.command(name='leave')
    async def leaveVC(self, ctx):
        """Leaves a voice channel"""
        voice_channel = ctx.voice_client

        if not voice_channel or not voice_channel.is_connected():
            embed = discord.Embed(title="", description="Error: Currently not connected to a voice channel", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            cleanup(ctx)
            await ctx.send('Disconnected from voice channel')

    # Instantiate Player
    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = _Player(ctx)
            self.players[ctx.guild.id] = player

        return player

    # Cleanup after disconnect
    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    # Add Item to Queue
    @commands.command(name='play', aliases=['p'])
    async def addSong(self, ctx, search: str):
        """Adds song to queue and plays it."""
        voice_channel = ctx.voice_client
        ctx.typing()
        if not voice_channel:
            await ctx.invoke(self.joinVC)
        
        player = self.get_player(ctx)
        source = await _YTDLSource.create_source(ctx, search, loop=None, download=False)
        await player.queue.put(source)
    @addSong.error
    async def addSong_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="", description="Error: Disallowed input type", color=discord.Color.red())
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="", description=ERROR_MISSINGARG.format(argument='Search Parameters(string | url)'), color=discord.Color.red())
            await ctx.send(embed=embed)

    # Pause Playback
    @commands.command(name='pause')
    async def pauseSong(self, ctx):
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
    @commands.command(name='resume')
    async def resumeSong(self, ctx):
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
    @commands.command(name='skip')
    async def skipSong(self, ctx):
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
    @commands.command(name='remove', aliases=['rm'])
    async def removeSong(self, ctx, pos: int=None):
        """Removes Song from queue"""
        voice_channel = ctx.voice_client

        if not voice_channel or not voice_channel.is_connected():
            embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
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
    @commands.command(name='clear', aliases=['cl', 'clr', 'cr'])
    async def clearQueue(self, ctx):
        """Clears queue of songs"""
        voice_channel = ctx.voice_client

        if not voice_channel or not voice_channel.is_connected():
            embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        player.queue._queue.clear()
        embed = discord.Embed(title="", description="Notice: Queue has been cleared", color=discord.Color.blue())
        await ctx.send(embed=embed)

    # Display Queue
    @commands.command(name='queue', aliases=['q'])
    async def displayQueue(self, ctx):
        """Display song queue"""
        voice_channel = ctx.voice_client

        if not voice_channel or not voice_channel.is_connected():
            embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
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
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

    # Now Playing
    @commands.command(name='np', aliases=['current', 'song', 'currentsong', 'playing'])
    async def currentSong(self, ctx):
        """Display current song"""
        voice_channel = ctx.voice_client

        if not voice_channel or not voice_channel.is_connected():
            embed = discord.Embed(title="", description="Notice: Not currently connected to a voice channel", color=discord.Color.blue())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
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
