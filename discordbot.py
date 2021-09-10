import os
import discord
from discord.ext import commands
import youtube_dl
from requests import get
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
# from keep_alive import keep_alive
# keep_alive()

client = commands.Bot(command_prefix="-")


YDL_OPTIONS = {
        'format': 'bestaudio',
        'noplaylist': 'True'
}

now_playing = ""
queue = []
queue_of_titles = []
got_stopped = False


def add_list_queue_item_(queue_url):
    global queue_of_titles
    data = search(queue_url)
    video_title = data['title']
    queue_of_titles.append(video_title)


def search(arg):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            get(arg)
        except:
            video = ydl.extract_info(f"ytsearch:{arg}",
                                     download=False)['entries'][0]
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
async def list(ctx):
    await ctx.send("Queue: ")
    await ctx.send(queue_of_titles)


@client.command()
async def raw(ctx):
    await ctx.send("Raw queue:")
    await ctx.send(queue)


@client.command(description="""Either you use a URL,
                            or just the name of the video you want to play""",
                aliases=["p"])
async def play(ctx, *url):
    global now_playing
    global queue
    # QUEUE SYSTEM
    if now_playing != "":
        queue.append(url)
        add_list_queue_item_(url)
        await ctx.send("Gonna play this song after the current song ends.")
    elif now_playing == "":
        song_there = os.path.isfile("song.webm")
        try:
            if song_there:
                os.remove("song.webm")
        except PermissionError:
            await ctx.send("PermissionError: There is still a song playing")
            return
        try:
            voicechannel_author = ctx.message.author.voice.channel
            if voicechannel_author:
                voiceChannel = discord.utils.get(ctx.guild.voice_channels,
                                                 name=str(voicechannel_author))
                await voiceChannel.connect()
                voice = discord.utils.get(client.voice_clients,
                                          guild=ctx.guild)
                ydl_opts = {'format': '249/250/251'}
                data = search(url)
                final_url = data.get('webpage_url')
                now_playing = final_url
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download((final_url,))
                for file in os.listdir("./"):
                    if file.endswith(".webm"):
                        os.rename(file, "song.webm")
                        voice.play(discord.FFmpegOpusAudio("song.webm"),
                                   after=lambda x: clear_np(ctx))
        except AttributeError:
            await ctx.send('''You need to be in a voice channel
                            to execute this command.''')


def clear_np(ctx):
    global now_playing
    global queue
    global got_stopped
    if got_stopped is False:
        now_playing = ""
        next_song(ctx)
    else:
        return


def next_song(ctx):
    global now_playing
    global queue
    if queue != "":
        voicechannel_author = ctx.message.author.voice.channel
        try:
            if voicechannel_author:
                voice = discord.utils.get(client.voice_clients,
                                          guild=ctx.guild)
                ydl_opts = {'format': '249/250/251'}
                data = search(queue[0])
                final_url = data.get('webpage_url')
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download((final_url,))
                for file in os.listdir("./"):
                    if file.endswith(".webm"):
                        os.rename(file, "song.webm")
                        voice.play(discord.FFmpegOpusAudio("song.webm"),
                                   after=lambda x: clear_np(ctx))
                        now_playing = "not empty!"
                        queue.pop(0)
        except AttributeError:
            ctx.send('''You need to be in a voice channel
                        to execute this command.''')


@client.command()
async def leave(ctx):
    global now_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if is_connected(ctx):
        await voice.disconnect(force=False)
    else:
        await ctx.send('Bot currently not in the channel.')


@client.command()
async def stop(ctx):
    global now_playing
    global got_stopped
    got_stopped = True
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
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
            video_title = info_dict.get('title')
            message = discord.Embed(title="Now Playing:")
            message.add_field(name=str(video_title),
                              value=str(now_playing))
            await ctx.send(embed=message)

client.run(TOKEN)
