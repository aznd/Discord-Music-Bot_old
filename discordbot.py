import os
import discord
from discord.ext import commands
import youtube_dl
from requests import get


client = commands.Bot(command_prefix="!")

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']

def search(arg):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            get(arg)
        except:
            video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else:
            video = ydl.extract_info(arg, download=False)
    return video

def is_connected(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()

@client.event
async def on_ready():
    print('Bot is ready.')


@client.command()
async def play(ctx, *url):
    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
    except PermissionError:
        await ctx.send("PermissionError: There is still a song playing")
        return
    try:
        voicechannel_author =  ctx.message.author.voice.channel
        if voicechannel_author:
            voiceChannel = discord.utils.get(ctx.guild.voice_channels, name=str(voicechannel_author))
            await voiceChannel.connect()
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            }
            data = search(url)
            final_url = data.get('webpage_url')
            print(final_url)
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download((final_url,))
                for file in os.listdir("./"):
                    if file.endswith(".mp3"):
                        os.rename(file, "song.mp3")
                        voice.play(discord.FFmpegOpusAudio("song.mp3"))
    except AttributeError:
        await ctx.send('You need to be in a voice channel to execute this command.')

@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if is_connected(ctx):
        await voice.disconnect()
    else:
        await ctx.send('Bot currently not in the channel.')

@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    is_playing = voice.is_playing()
    if is_playing:
        voice.stop()
    else:
        await ctx.send('Bot is currently not playing anything.')

@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    is_playing = voice.is_playing()
    if is_playing:
        voice.pause()
    else:
        await ctx.send('Bot is currently not playing anything.')

@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    is_paused = voice.is_paused()
    if is_paused:
        voice.resume()
    else:
        await ctx.send('Bot is currently not paused.')

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}

@client.command()
async def searchd(ctx, arg):
    await ctx.send(search(arg))

client.run(TOKEN)
