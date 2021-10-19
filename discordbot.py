import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
client = commands.Bot(command_prefix="-")


YDL_OPTIONS = {
        'format': 'bestaudio',
        'no-abort-on-error': 'True'
}

now_playing = ""
queue_of_urls = []
queue_of_titles = []
video_title = ""
has_joined = False
warn_user_not_in_channel = ("You need to be in a voice channel "
                            "to use this command.")
adding_playlist = ("Adding playlist to the queue. "
                   "(If your provided link isn't a playlist, "
                   "please send @aznd the link.)")


def add_list_queue_item(queue_url):
    global queue_of_titles
    global video_title
    data = search(queue_url)
    video_title = data['title']
    queue_of_titles.append(video_title)


def search(arg):
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
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
    now_playing = ""
    next_song(ctx)


def next_song(ctx):
    global now_playing
    global queue_of_urls
    global queue_of_titles
    voicechannel_author = ctx.message.author.voice.channel
    if voicechannel_author:
        voice = discord.utils.get(client.voice_clients,
                                  guild=ctx.guild)
        if voice.is_playing():
            voice.stop()
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                ydl.download((queue_of_urls[0],))
            for file in os.listdir("./"):
                if file.endswith(".webm"):
                    os.rename(file, "song.webm")
                    voice.play(discord.FFmpegOpusAudio("song.webm"),
                               after=lambda x: clear_np(ctx))
                    now_playing = queue_of_titles[0]
                    queue_of_titles.pop(0)
                    queue_of_urls.pop(0)
        except IndexError:
            ctx.send("Queue is now empty.")


def clear_all():
    global now_playing
    queue_of_titles.clear()
    queue_of_urls.clear()
    now_playing = ""


@client.event
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Unknown command! Use -help to see all commands.')


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


@client.command()
async def join(ctx):
    global has_joined
    voicechannel_author = ctx.message.author.voice.channel
    voiceChannel = discord.utils.get(ctx.guild.voice_channels,
                                     name=str(voicechannel_author))
    try:
        await voiceChannel.connect()
        has_joined = True
    except Exception as e:
        await ctx.send(e)


@client.command(aliases=['p'])
async def play(ctx, *, url):
    global now_playing
    global queue_of_urls
    global queue_of_titles
    # If no URL was provided, warn the user.
    if url == "":
        await ctx.send("You need to provide a url, or a video name.")
    # If there is something currently playing, just add it to the queue.
    elif now_playing != "":
        if "list" in str(url):
            await ctx.send(adding_playlist)
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                data = ydl.extract_info(url, download=False)
                for i in data['entries']:
                    queue_of_urls.append(i['webpage_url'])
                    queue_of_titles.append(i['title'])
        else:
            data = search(url)
            final_url = data.get('webpage_url')
            queue_of_urls.append(final_url)
            add_list_queue_item(url)
            await ctx.send("Added Song to the queue.")
    # If nothing is currently playing, we can actually play it immediately.
    elif now_playing == "":
        # We have a playlist
        if "list" in url:
            await ctx.send(adding_playlist)
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                data = ydl.extract_info(url, download=False)
                for i in data['entries']:
                    queue_of_urls.append(i['webpage_url'])
                    queue_of_titles.append(i['title'])
                ydl.download((queue_of_urls[0],))
                now_playing = data['entries'][0]['title']
                song_there = os.path.isfile("song.webm")
                if song_there:
                    os.remove("song.webm")
                voicechannel_author = ctx.message.author.voice.channel
                if voicechannel_author:
                    voiceChannel = discord.utils.get(ctx.guild.voice_channels,
                                                     name=str(voicechannel_author))
                    if not has_joined:
                        await voiceChannel.connect()
                    voice = discord.utils.get(client.voice_clients,
                                              guild=ctx.guild)
                    for file in os.listdir("./"):
                        if file.endswith(".webm"):
                            os.rename(file, "song.webm")
                            voice.play(discord.FFmpegOpusAudio("song.webm"),
                                       after=lambda x: clear_np(ctx))
        # We dont have a playlist
        else:
            data = search(url)
            final_url = data.get('webpage_url')
            now_playing = data.get('title')
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                ydl.download((final_url,))
                voicechannel_author = ctx.message.author.voice.channel
                voiceChannel = discord.utils.get(ctx.guild.voice_channels,
                                                 name=str(voicechannel_author))
                if not has_joined:
                    await voiceChannel.connect()
                for file in os.listdir("./"):
                    if file.endswith(".webm"):
                        os.rename(file, "song.webm")
                        voice = discord.utils.get(client.voice_clients,
                                                  guild=ctx.guild)
                        voice.play(discord.FFmpegOpusAudio("song.webm"),
                                   after=lambda x: clear_np(ctx))


@client.command(aliases=['l'])
async def leave(ctx):
    global now_playing
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if is_connected(ctx):
        await voice.disconnect(force=False)
        clear_all()
        message = await ctx.send("Bot left the channel: "
                                 + str(voice.channel)
                                 + " and cleared the queue.")
        await message.add_reaction("👋")
    else:
        await ctx.send('Bot currently not in the channel.')


@client.command()
async def stop(ctx):
    global now_playing
    global queue_of_titles
    global queue_of_urls
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    is_playing = voice.is_playing()
    if is_playing:
        queue_of_titles = []
        queue_of_urls = []
        await ctx.send("Bot stopped and cleared the queue. (If you didnt want to clear the queue, use the pause command instead of stop.)")
        voice.stop()
        now_playing = ""
    else:
        await ctx.send('Bot is currently not playing anything.')


@client.command()
async def skip(ctx):
    global now_playing
    global video_title
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    now_playing = ""
    voice.stop()
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
