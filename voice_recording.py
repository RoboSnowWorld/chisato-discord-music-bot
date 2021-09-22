import wave

import discord
import os
import blacklisted_words
import settings


def vc_required(func):
    async def get_vc(self, msg, *args):
        vc = await self.get_vc(msg)
        if not vc:
            return
        await func(self, msg, vc)
    return get_vc


class Client(discord.Client):

    voice_settings = settings.voice_settings

    commands_description = settings.commands_description

    blacklisted_words = blacklisted_words.blacklisted_words

    blacklisted_channels = []
    admin_commands = settings.admin_commands
    user_commands = settings.user_commands

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connections = {voice.guild.id: voice for voice in self.voice_clients}
        self.playlists = {}
        self.voices = {}
        self.moder_channels = {}
        self.user_want_to_stop = {}
        self.helpembed = discord.Embed(colour=discord.Colour.green())
        self.channelembed = discord.Embed(colour=discord.Colour.green())
        self.blacklistembed = discord.Embed(colour=discord.Colour.green())

        self.commands = {
            'globals': {
                '1984start': self.start_moderation,
                '1984stop': self.stop_moderation,
                '1984channel': self.channel,
                '1984report': self.report,
                '1984help': self.help,
                '1984blacklist': self.blacklist,
            },
            'channel': {
                'voice': self.set_voicechannel,
                'moderator': self.set_moderatorchannel,
            },
            'blacklist': {
                'add': self.add_to_blacklist,
                'remove': self.remove_from_blacklist,
                'clear': self.clear_blacklist,
                'all': self.show_blacklist,
            }
        }

        self.helpembed.set_image(url='https://images.pexels.com/photos/4973819/pexels-photo-4973819.jpeg')
        self.helpembed.set_author(name="Commands 1984.py", icon_url='https://i.imgur.com/A9UIbk6.png')
        for command in self.commands_description:
            self.helpembed.add_field(name=command, value=self.commands_description[command], inline=True)

        for command in self.commands_description:
            if 'channel' in command: self.channelembed.add_field(name=command, value=self.commands_description[command],
                                                              inline=True)

        self.channelembed.set_image(url='https://images.pexels.com/photos/4829828/pexels-photo-4829828.jpeg')
        for command in self.commands_description:
            if 'blacklist' in command: self.blacklistembed.add_field(name=command, value=self.commands_description[command],
                                                              inline=True)

        self.blacklistembed.set_image(url='https://images.pexels.com/photos/4973817/pexels-photo-4973817.jpeg')
        self.blacklistembed.set_author(name="Bad words will be automatically deleted from the moderated text channels",
                                       icon_url='https://i.imgur.com/A9UIbk6.png')


    async def get_vc(self, message):
        if message.guild.id not in self.voices:
            await message.channel.send("Select moderated voice channel | 1984channel voice")
            return
        channel = self.voices[message.guild.id]
        connection = self.connections.get(message.guild.id)
        if connection:
            if connection.channel is self.voices[message.guild.id]:
                return connection
            await connection.move_to(channel)
            return connection
        else:
            vc = await channel.connect()
            self.connections.update({message.guild.id: vc})
            return vc

    async def clear_blacklist(self, msg):
        for channel in msg.guild.channels:
            if channel in self.blacklisted_channels: self.blacklisted_channels.remove(channel)
        await msg.channel.send('successfully')

    async def show_blacklist(self, msg):
        mentions = '['
        await msg.channel.send("Now bad words are automatically deleted from:")
        for channel in msg.guild.channels:
            if channel in self.blacklisted_channels:
                mentions += channel.mention
        mentions += ']'
        await msg.channel.send(content=mentions)

    async def blacklist(self, msg):
        try:
            cmd = msg.content.split()[1]
        except IndexError:
            await msg.channel.send(embed=self.blacklistembed)
            return

        try:
            await self.commands['blacklist'][cmd](msg)
        except KeyError:
            await msg.channel.send("Unknown command. Use 1984help")

    async def add_to_blacklist(self, msg):
        if msg.channel in self.blacklisted_channels:
            await msg.channel.send("This channel is already moderated")
            return
        self.blacklisted_channels.append(msg.channel)
        await msg.channel.send(f'{msg.channel.mention} now is moderated')

    async def remove_from_blacklist(self, msg):
        try:
            self.blacklisted_channels.remove(msg.channel)
            await msg.channel.send('successfully')
        except ValueError:
            await msg.channel.send("This text channel is currently not moderated")

    async def on_message(self, msg):
        if not msg.content:
            return
        cmd = msg.content.split()[0]
        if cmd[0:4] == '1984':
            perms = msg.author.guild_permissions.administrator
            if cmd in self.admin_commands and not perms:
                await msg.channel.send("`1984report` to report user | Only administrators can configure the bot")
                return
            if cmd in self.commands['globals']:
                await self.commands['globals'][cmd](msg)
            else:
                await msg.channel.send('Unknown command. Use 1984help')
        else:
            if msg.channel in self.blacklisted_channels: await self.check_msg(msg)

    async def check_msg(self, msg):
        if msg.author.bot:
            return
        for word in self.blacklisted_words:
            if word in msg.content:
                try:
                    await self.moder_channels[msg.guild.id].send(
                        f'{msg.author.mention} is using bad words in {msg.channel.mention}')
                except KeyError:
                    pass
                await msg.delete()
                return


    async def help(self, msg):
        await msg.channel.send(embed=self.helpembed)

    @vc_required
    async def start_moderation(self, msg, vc):
        self.user_want_to_stop[msg.guild.id] = False
        await msg.channel.send(f'{self.voices[msg.guild.id].mention} Voice moderation successfully started')
        await self.start_recording(msg)

    @vc_required
    async def start_recording(self, msg, vc):
        vc.start_recording(discord.Sink(encoding='wav', filters=self.voice_settings), self.finished_callback, msg)

    @vc_required
    async def stop_moderation(self, msg, vc):
        if vc.recording:
            await msg.channel.send("Voice moderation successfully stopped")
            self.user_want_to_stop[msg.guild.id] = True
            vc.stop_recording()
            await vc.disconnect()
        else:
            await msg.channel.send(f'Voice moderation in {self.voices[msg.guild.id].mention} is not launched now | 1984start')
            return

    @vc_required
    async def report(self, msg, vc):
        if msg.guild.id not in self.moder_channels:
            await msg.channel.send("Select channel for receiving reports | 1984channel moderator")
            return
        channel = self.moder_channels[msg.guild.id]
        if not msg.mentions: return
        user_id = msg.mentions[0].id
        user = msg.mentions[0]
        if not vc.recording or self.user_want_to_stop[msg.guild.id]:
            await msg.channel.send(f'Voice moderation in {self.voices[msg.guild.id].mention} is not launched now | 1984start')
            return
        try:
            ssrc = vc.get_ssrc(user_id)
        except KeyError:
            await msg.channel.send("Too much time has passed since the violation")
            return

        report_msg = await channel.send(f'Report to {user.mention}')
        await report_msg.add_reaction(emoji='✅')
        ssrc = str(ssrc)
        user_voice = ssrc + '_latest.wav'
        try:
            with open(ssrc + '.pcm', 'rb') as pcm:
                data = pcm.read()
                pcm.close()
            wav_file = user_voice
            with wave.open(wav_file, 'wb') as f:
                f.setnchannels(vc.decoder.CHANNELS)
                f.setsampwidth(vc.decoder.SAMPLE_SIZE // vc.decoder.CHANNELS)
                f.setframerate(vc.decoder.SAMPLING_RATE)
                f.writeframes(data)
                f.close()
            f = open(user_voice, 'rb')
            await channel.send(file=discord.File(fp=f, filename=user_voice))
            f.close()
            os.remove(user_voice)
        except FileNotFoundError:
            pass
        user_voice = ssrc + '.wav'
        try:
            f = open(user_voice, 'rb')
            await channel.send(file=discord.File(fp=f, filename=user_voice))
            f.close()
        except FileNotFoundError:
            pass
        await msg.channel.send(f"Report to {user.mention} successfully sent")

    async def channel(self, message):
        try:
            cmd = message.content.split()[1]
        except IndexError:
            await message.channel.send(embed=self.channelembed)
            return

        try:
            await self.commands['channel'][cmd](message)
        except KeyError:
            await message.channel.send("Unknown command. Use 1984help")

    async def set_voicechannel(self, msg):
        user = msg.author
        try:
            channel = user.voice.channel
        except AttributeError:
            await msg.channel.send("You are not in voice")
            return
        self.voices[msg.guild.id] = channel
        await msg.channel.send(f'{channel.mention} now will be moderated')

    async def set_moderatorchannel(self, msg):
        self.moder_channels[msg.guild.id] = msg.channel
        await msg.channel.send(f'{msg.channel.mention} selected for receiving reports')

    async def finished_callback(self, sink, msg, *args):
        if self.user_want_to_stop[msg.guild.id]:
            return
        await self.start_recording(msg)

    async def on_voice_state_update(self, member, before, after):
        if member.id != self.user.id:
            return
        if member.guild.id not in self.connections and (not before.channel and after.channel):
            return
        if before.channel is after.channel:
            return

        connection = self.connections.get(member.guild.id)
        self.user_want_to_stop[member.guild.id] = True
        connection.cleanup()
        del self.connections[member.guild.id]
