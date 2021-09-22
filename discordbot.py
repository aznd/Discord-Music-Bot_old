import os
import discord
from discord.ext import commands
from keep_alive import keep_alive
import youtube_dl
TOKEN = os.environ['TOKEN']
keep_alive()
client = commands.Bot(command_prefix="-")


YDL_OPTIONS = {
        'format': 'bestaudio',
        'noplaylist': 'True'
}

now_playing = ""
now_playing_url = ""
now_playing_title = ""
queue_of_urls = []
queue_of_titles = []
got_stopped = False
video_title = ""
warn_user_not_in_channel = "You need to be in a voice channel to use this command."


def add_list_queue_item_(queue_url):
    global queue_of_titles
    global video_title
    data = search(queue_url)
    video_title = data['title']
    queue_of_titles.append(video_title)


def search(arg):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        if arg.startswith('http'):
            video = ydl.extract_info(arg, download=False)
        else:
            video = ydl.extract_info(f"ytsearch:{arg}",
                                     download=False)['entries'][0]
    return video


def is_connected(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()


def clear_np(ctx):
    global now_playing
    global got_stopped
    if got_stopped is False:
        now_playing = ""
        next_song(ctx)
    else:
        return


def next_song(ctx):
    global now_playing
    global queue_of_urls
    global queue_of_titles
    if queue_of_urls != "":
        voicechannel_author = ctx.message.author.voice.channel
        try:
            if voicechannel_author:
                voice = discord.utils.get(client.voice_clients,
                                          guild=ctx.guild)
                data = search(queue_of_titles[0])
                final_url = data.get('webpage_url')
                with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                    ydl.download((final_url,))
                for file in os.listdir("./"):
                    if file.endswith(".webm"):
                        os.rename(file, "song.webm")
                        voice.play(discord.FFmpegOpusAudio("song.webm"),
                                   after=lambda x: clear_np(ctx))
                        now_playing = queue_of_titles[0]
                        queue_of_titles.pop(0)
                        queue_of_urls.pop(0)
        except AttributeError:
            ctx.send(warn_user_not_in_channel)


def clear_all():
    global now_playing
    global now_playing_title
    global now_playing_url
    queue_of_titles.clear()
    queue_of_urls.clear()
    now_playing = ""
    now_playing_title = ""
    now_playing_url = ""


@client.event
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Unknown command! Use -help to get all commands.')


@client.command(aliases=['queue'])
async def list(ctx):
    if len(queue_of_titles) == 0:
        await ctx.send("Nothing is in the queue.")
    else:
        global video_title
        i = 1
        embed = discord.Embed(title="Queue:",
                              description=" ",
                              color=0xFF5733)
        for e in queue_of_titles:
            embed.add_field(name=str(i) + ":",
                            value=str(e))
            i += 1
        await ctx.send(embed=embed)


@client.command()
async def raw(ctx):
    await ctx.send("Raw queue:")
    await ctx.send(queue_of_urls)


@client.command()
async def clear(ctx):
    clear_all()
    await ctx.send("Successfully cleared the queue!")


@client.command(aliases=['p'])
async def play(ctx, *, url):
    global now_playing
    global queue_of_urls
    global now_playing_title
    global now_playing_url
    # QUEUE SYSTEM
    if url == "":
        await ctx.send("You need to provide a url, or a video name.")
    else:
        if now_playing != "":
            queue_of_urls.append(url)
            add_list_queue_item_(url)
            await ctx.send("Added Song to the queue.")
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
                    now_playing = data.get('title')
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        ydl.download((final_url,))
                    for file in os.listdir("./"):
                        if file.endswith(".webm"):
                            os.rename(file, "song.webm")
                            voice.play(discord.FFmpegOpusAudio("song.webm"),
                                       after=lambda x: clear_np(ctx))
            except AttributeError:
                await ctx.send(warn_user_not_in_channel)


@client.command(aliases=['l'])
async def leave(ctx):
    global now_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if is_connected(ctx):
        await voice.disconnect(force=False)
        clear_all()
        message = await ctx.send("Bot left the channel: " + str(voice.channel) + " and cleared the queue.")
        await message.add_reaction("👋")
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
async def skip(ctx):
    global now_playing
    global got_stopped
    global video_title
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    now_playing = ""
    voice.stop()
    got_stopped = True
    video_title = ""
    next_song(ctx)


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
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    is_playing = voice.is_playing()
    if is_playing is None:
        await ctx.send("Nothing is currently playing.")
    else:
        data = search(now_playing)
        video_url = data.get('webpage_url')
        video_title = data.get('title')
        video_thumbnail = data.get('thumbnail')
        message = discord.Embed(title="Now Playing:")
        message.add_field(name=str(video_title),
                          value=str(video_url))
        message.set_thumbnail(url=video_thumbnail)
        await ctx.send(embed=message)

client.run(TOKEN)
