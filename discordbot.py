import os
import discord
from discord.ext import commands
import youtube_dl
from requests import get
from typing import Union
#from keep_alive import keep_alive
#keep_alive()

client = commands.Bot(command_prefix="-")
#my_secret = os.environ["DISCORD_TOKEN"]


YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
now_playing = ""
queue = []
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
    global now_playing
    if now_playing != "":
        queue.append(url)
    elif now_playing == "":
        song_there = os.path.isfile("song.webm")
        try:
            if song_there:
                os.remove("song.webm")
        except PermissionError:
            await ctx.send("PermissionError: There is still a song playing")
            return
        try:
            voicechannel_author =  ctx.message.author.voice.channel
            if voicechannel_author:
                voiceChannel = discord.utils.get(ctx.guild.voice_channels, name=str(voicechannel_author))
                await voiceChannel.connect()
                voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
                ydl_opts = {'format': '249/250/251',}
                data = search(url)
                final_url = data.get('webpage_url')
                now_playing = final_url
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download((final_url,))
                for file in os.listdir("./"):
                    if file.endswith(".webm"):
                        os.rename(file, "song.webm")
                        voice.play(discord.FFmpegOpusAudio("song.webm"))
        except AttributeError:
            await ctx.send('You need to be in a voice channel to execute this command.')

@client.command()
async def leave(ctx):
    global now_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if is_connected(ctx):
        await voice.disconnect()
        now_playing = ""
    else:
        await ctx.send('Bot currently not in the channel.')

@client.command()
async def stop(ctx):
    global now_playing
    voice: Union[ VoiceProtocol , None ] = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice is None:
        print("yes")
    else:
        is_playing = voice.is_playing()
        if is_playing:
            voice.stop()
            now_playing = ""
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

@client.command()
async def np(ctx):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        if now_playing == "":
            await ctx.send("Nothing is currently playing.")
        else:
            info_dict = ydl.extract_info(now_playing, download=False)
            video_title = info_dict.get('title', None)
            message = discord.Embed(title = "Now Playing:")
            message.add_field(name = video_title, value = now_playing)
            await ctx.send(embed = message)
            print(queue)

