import discord
import lightbulb
from youtube_dl import *
from discord.ext import commands, tasks
from pytube import Playlist
import random
bot = commands.Bot(command_prefix='-', description="Music Bot. Type -help to see my commands.")


queue = []


def get_all_video_links(URL) :
    if 'www.youtube.com' in URL:
        if 'playlist' in URL :
            lst = []
            p = Playlist(URL)
            for video in p.videos :
                lst.append(video.watch_url)

            return lst
        else :
            return [URL]
    else:
        YDL_OPTIONS = {'default_search' : 'auto', 'format' : 'bestaudio', 'noplaylist' : 'True'}

        FFMPEG_OPTIONS = {'before_options' : '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options' : '-vn'}
        with YoutubeDL(YDL_OPTIONS) as ydl :
            info = ydl.extract_info(URL, download=False)
        print(info)
        print(len(info['entries']))

        if info['_type'] == 'playlist':
            return [f'https://www.youtube.com/watch?v={i["id"]}' for i in info['entries']]

async def playnext(ctx, q=None):

    YDL_OPTIONS = {'default_search' : 'auto', 'format' : 'bestaudio', 'noplaylist' : 'True'}

    FFMPEG_OPTIONS = {'before_options' : '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options' : '-vn'}
    voice = ctx.message.guild.voice_client

    global queue
    with YoutubeDL(YDL_OPTIONS) as ydl :
        if q != None:
            try:

                info = ydl.extract_info(q, download=False)
                a = info['entries'][0]['formats'][0]['url']
                print(info)
                queue.append([a, f'https://www.youtube.com/watch?v={info["id"]}'])
                if voice.is_playing() :
                    await ctx.send(
                        f'**Queued:** {info["title"]}\n**Uploaded by**: {info["uploader"]} \n**URL:** <https://www.youtube.com/watch?v={info["id"]}>')
                else :
                    idk = queue[0][0]
                    queue.pop(0)
                    voice.play(discord.FFmpegPCMAudio(idk, **FFMPEG_OPTIONS))
            except :
                info = ydl.extract_info(q, download=False)
                a = info['url']
                print(info)

                queue.append([a, f'https://www.youtube.com/watch?v={info["id"]}'])
                if voice.is_playing() :
                    await ctx.send(
                        f'**Queued:** {info["title"]}\n**Uploaded by**: {info["uploader"]} \n**URL:** <https://www.youtube.com/watch?v={info["id"]}>')


                elif len(queue) == 0 :
                    await ctx.send(
                        f'**Playing:** {info["title"]}\n**Uploaded by**: {info["uploader"]} \n**URL:** <https://www.youtube.com/watch?v={info["id"]}>')
                    idk = queue[0][0]
                    voice.play(discord.FFmpegPCMAudio(idk, **FFMPEG_OPTIONS))
                else :
                    await ctx.send(
                        f'**Playing:** {info["title"]}\n**Uploaded by**: {info["uploader"]} \n**URL:** <https://www.youtube.com/watch?v={info["id"]}>')
                    idk = queue[0][0]
                    queue.pop(0)
                    voice.play(discord.FFmpegPCMAudio(idk, **FFMPEG_OPTIONS))
        else:
            if voice.is_playing() == False and len(queue) != 0:
                info = ydl.extract_info(queue[0][1], download=False)
                await ctx.send(
                    f'**Playing:** {info["title"]}\n**Uploaded by**: {info["uploader"]} \n**URL:** <https://www.youtube.com/watch?v={info["id"]}>')
                idk = queue[0]
                idk = idk[0]
                queue.pop(0)
                voice.play(discord.FFmpegPCMAudio(idk, **FFMPEG_OPTIONS))




@bot.command(name="play", brief='Play Songs and PLaylists from Youtube with URL or any query words. Add --shuffle optiom to shuffle playlist before adding to queue', pass_ctx=True)

async def play(ctx, *stri: str):
    w = stri[0]
    shuffle = False
    for i in stri[1:]:
        if not '--shuffle' in i:

            w+=f' {i}'
        else:
            shuffle = True
    try:
        channel = ctx.message.author.voice.channel
        await channel.connect()
        # await ctx.send("I\'m in")
    except:
        await ctx.send("You need to be connected to a voice channel in order for me to join. Or I don't have the right to join your voice channel.")
        pass


    global ctx_global
    ctx_global = ctx

    lst = get_all_video_links(w)
    if shuffle:
        random.shuffle(lst)
    for q in lst:
        await playnext(ctx, q)


    try:
        check_if_finished.start()
    except:
        try:
            check_if_finished.start()
        except:
            pass






@bot.command(name="queue", brief='Show current queue. Delete song from queue with --delete option', pass_ctx=True)

async def Queue(ctx, *args):
    delete = False
    delete_song_arg = ''
    for n, i in enumerate(args):
        if delete:
            delete_song_arg += f' {i}'
        if i == '--delete':
            delete = True
    if delete:
        delete_song_arg = delete_song_arg[1:]
        



    global queue
    stri = ''
    YDL_OPTIONS = {'default_search' : 'auto', 'format' : 'bestaudio', 'noplaylist' : 'True'}
    with YoutubeDL(YDL_OPTIONS) as ydl :
        for n, i in enumerate(queue):
            info = ydl.extract_info(i[1], download=False)
            if delete:
                if delete_song_arg in str(info):
                    queue.pop(n)
                else:
                    stri+=f'{n+1}. **Title:** {info["title"]} **Uploaded by**: {info["uploader"]} **URL:** <https://www.youtube.com/watch?v={info["id"]}> \n'
            else:
                stri += f'{n + 1}. **Title:** {info["title"]} **Uploaded by**: {info["uploader"]} **URL:** <https://www.youtube.com/watch?v={info["id"]}> \n'
        
    if not stri == '':
        await ctx.send(
            str(stri))

    else:
        await ctx.send('Queue is empty. Use *-play [URL/QUERY]* to play something.')


@bot.command(name="stop", brief='Stop playing song and delete queue', pass_ctx=True)

async def stop(ctx):

    global queue
    queue = []
    voice = ctx.message.guild.voice_client
    voice.stop()
    try:
        check_if_finished.cancel()
    except:
        pass
    await ctx.send('Playing stopped and Queue cleared.')

@bot.command(name="pause", brief='Pause the playing song', pass_ctx=True)
async def pause(ctx):
    try:
        check_if_finished.cancel()
    except:
        pass
    voice = ctx.message.guild.voice_client
    voice.pause()
    await ctx.send('Playing audio paused. Use *-resume* to resume.')

@bot.command(name="resume", brief='Resume the paused song', pass_ctx=True)
async def resume(ctx):

    voice = ctx.message.guild.voice_client
    await ctx.send('Audio resumed.')
    voice.resume()

    try:
        check_if_finished.start()
    except:
        try:
            check_if_finished.start()
        except:
            pass
@bot.command(name="skip", brief='Skip currently playing song', pass_ctx=True)
async def skip(ctx):
    try :
        check_if_finished.cancel()


    except :
        try :
            check_if_finished.stop()
        except :
            pass

    voice = ctx.message.guild.voice_client
    voice.stop()
    await playnext(ctx)
    try :
        check_if_finished.start()
    except :
        check_if_finished.start()

global xyz
xyz = 0


@bot.command(name="shuffle", brief='randomly shuffle the queue', pass_ctx=True)
async def shuffle(ctx):
    global queue
    random.shuffle(queue)
    global ctx_global
    await Queue(ctx_global)





@tasks.loop(seconds=1)
async def check_if_finished():
    global xyz
    if xyz == 100:
        xyz = 0
    else:
        xyz +=1
    strii = ''
    for i in range(xyz):
        strii += '.'
    print('\r', 'checking'+strii, end='')


    global ctx_global
    voice = ctx_global.message.guild.voice_client

    # print(voice.is_playing())
    if not voice.is_playing():
        await playnext(ctx_global)






bot.run("NzE0NDUxMjQ0MzMyMjIwNDgw.Xsu2kg.9u75_u2BoTxjj8ogNy_CQ3OgAeo")