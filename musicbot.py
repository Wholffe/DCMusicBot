import discord
import yt_dlp
from discord.ext import commands

FFMPEG_OPTIONS = {'options': '-vn'}
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch'
}


class MusicBot(commands.Cog):

  def __init__(self, bot):
    self.client = bot
    self.queue = []

  @commands.command()
  async def play(self, ctx, *, search):
    try:
      voice_channel = ctx.author.voice.channel if ctx.author.voice else None
      if not voice_channel:
        return await ctx.send("You are not connected to a voice channel.")

      if not ctx.voice_client:
        await voice_channel.connect()

      async with ctx.typing():
        info = await self.get_info(search)
        if not info:
          return await ctx.send("Failed to retrieve the video information.")

        if isinstance(info, dict) and 'entries' in info:
          info = info['entries'][0]

        if 'url' not in info or 'title' not in info:
          return await ctx.send("Failed to retrieve the video URL or title.")

        url, title = info['url'], info['title']
        self.queue.append((url, title))
        await ctx.send(f"Added to queue: {title}")

        if not ctx.voice_client.is_playing():
          await self.play_next(ctx)
    except Exception as e:
      await ctx.send(f"An error occurred: {str(e)}")

  async def play_next(self, ctx):
    try:
      if self.queue:
        url, title = self.queue.pop(0)
        source = await discord.FFmpegOpusAudio.from_probe(
            url, **FFMPEG_OPTIONS)
        ctx.voice_client.play(
            source,
            after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
        await ctx.send(f"Now playing: {title}")
      elif not ctx.voice_client.is_playing():
        await ctx.send("Queue is empty. Use /play to add songs.")
    except Exception as e:
      await ctx.send(f"An error occurred while playing the song: {str(e)}")

  @commands.command()
  async def skip(self, ctx):
    try:
      if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped the current song.")
    except Exception as e:
      await ctx.send(f"An error occurred while skipping the song: {str(e)}")

  @commands.command()
  async def ping(self, ctx):
    await ctx.send('pong')

  @commands.command()
  async def djhelp(self, ctx):
    await ctx.send('Available commands:\n'
                   '/play <search> - Play a song from YouTube\n'
                   '/skip - Skip the current song\n'
                   '/ping - Ping the bot\n')

  async def get_info(self, search):
    try:
      with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(search, download=False)
      return info
    except Exception as e:
      print(f"Error fetching video information: {str(e)}")
      return None