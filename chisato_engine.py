import asyncio
import discord
from youtube_dl import YoutubeDL
import os

current_path = os.path.dirname(os.path.realpath(__file__))
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'False'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


class Bot(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__()
        discord.Intents.guilds = True
        self.queue_embed = discord.Embed(colour=discord.Colour.purple(), title='Chisato queue')
        self.help_embed = discord.Embed(colour=discord.Colour.purple())
        self.paused = {}
        self.queue = {}
        self.vc = {}
        self.commands_description = {

            '?help': 'Show commands description',
            '?play': 'Play music in the voice',
            '?play --mp3': 'You can add your file to queue. Attach it',
            '?stop': 'stop playing music',
            '?skip': 'skip track',
            '?queue': 'show queue',
            '?clear': 'clear queue',
            '?pause': 'pause playing',

        }
        self.commands = {

            '?help': self.show_help,
            '?play': self.play,
            '?stop': self.stop,
            '?skip': self.skip,
            '?queue': self.show_queue,
            '?clear': self.clear_queue,
            '?pause': self.pause,

        }

    async def on_ready(self):
        self.help_embed.set_author(name='Chisato music bot commands', icon_url='https://i.imgur.com/KoramfR.jpeg')
        for command in self.commands_description:
            self.help_embed.add_field(name=command, value=self.commands_description[command])

        self.queue_embed.set_image(url='https://i.imgur.com/KoramfR.jpeg')

    async def play_queue(self, guild):
        while True:
            if self.vc[guild].is_playing() or self.paused[guild]:
                await asyncio.sleep(0)
            elif self.queue[guild]:
                self.vc[guild].play(discord.FFmpegPCMAudio(source=self.queue[guild][0]['url']))
                self.queue[guild].pop(0)
            else:
                break

    async def on_message(self, message):
        if message.author == self.user:
            return
        if not message.guild:
            return

        if message.guild not in self.paused.keys():
            self.paused[message.guild] = False

        if message.content[0] != '?':
            return

        command = message.content.split()[0]
        try:
            await self.commands[command](message)
        except KeyError:
            await message.channel.send("Unknown command. Use ?help to see the command list")

    async def get_vc(self, command):
        if not command.author.voice:
            await command.channel.send("You must be in voice channel")
            return False
        else:
            voicechannel = command.author.voice.channel

        guild = command.guild

        try:
            self.vc[guild] = await voicechannel.connect()
        except discord.errors.ClientException:
            pass
        return True

    async def play(self, command):
        guild = command.guild

        if not await self.get_vc(command):
            return

        if guild not in self.queue:
            self.queue[guild] = []

        if guild in self.paused and self.paused[guild]:
            self.paused[guild] = False
            self.vc[guild].resume()
            await command.channel.send("_Resumed._")
            return

        if '--mp3' in command.content:
            try:
                attachment = command.attachments[0]
            except IndexError:
                await command.channel.send("Please, attach `file with music`")
                return
            attachment_path = current_path + '/' + attachment.filename
            await attachment.save(fp=attachment_path)
            self.queue[guild].append(
                {'title': attachment.filename,
                 'url': attachment_path,}
            )
            await command.channel.send(f'`{attachment.filename}` added to queue')
            if self.vc[guild].is_playing():
                return
            else:
                await self.play_queue(command.guild)
            return

        try:
            check = command.content.split()[1]
        except IndexError:
            await command.channel.send("`?play [url]`")
            return

        with YoutubeDL(YDL_OPTIONS) as ydl:
            entered_url = command.content[6:]
            info = ydl.extract_info('ytsearch:' + entered_url, download=False)

        url = info['entries'][0]['formats'][0]['url']
        title = info['entries'][0]['title']
        self.queue[guild].append(
            {'url': url,
             'title': title}
        )
        await command.channel.send(f'`{title}` added to queue')
        if self.vc[guild].is_playing():
            return
        else:
            await self.play_queue(command.guild)

    async def show_help(self, command):
        await command.channel.send(embed=self.help_embed)

    async def skip(self, command):
        if not await self.get_vc(command):
            return
        self.vc[command.guild].stop()
        await command.channel.send("_track skipped._")

    async def show_queue(self, command):
        await command.channel.send("Chisato queue:")
        try:
            for track in self.queue[command.guild]:
                await command.channel.send(f"{track['title']}")
        except KeyError:
            pass

    async def clear_queue(self, command):
        guild = command.guild
        if not await self.get_vc(command):
            return
        self.queue[guild] = []
        self.vc[guild].stop()
        await command.channel.send("_your queue cleared._")

    async def stop(self, command):
        guild = command.guild
        await self.clear_queue(command)
        await self.vc[guild].disconnect()
        self.vc[guild].cleanup()
        self.paused[guild] = False
        await command.channel.send("_Successfully stopped._")

    async def pause(self, command):
        if not await self.get_vc(command):
            return
        self.vc[command.guild].pause()
        self.paused[command.guild] = True
        await command.channel.send("_Paused._")
