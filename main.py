import discord
import voice_recording

intents = discord.Intents.default()
client = voice_recording.Client(intents=intents)
client.run('token')

# 1984help to see the commands list
# https://github.com/Sheepposu/discord.py/blob/master/examples/receive_vc_audio.py needed
