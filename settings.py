# filters for discord.Sink
voice_settings = {
    'time': 20,
    'users': [],
    'max_size': 0,
}

# used in help embeds
commands_description = {
    '1984start': '`start voice moderation`',
    '1984stop': '`stop voice moderation`',
    '1984channel voice': '`select moderated voice channel`',
    '1984channel moderator': '`select channel for receiving reports`',
    '1984report': '`Report user (with mention)`',
    '1984blacklist add': '`Moderate text channel`',
    '1984blacklist remove': '`Do not moderate text channel`',
    '1984blacklist clear': '`Clear list of moderated text channels`',
    '1984blacklist all': '`Show all moderated text channels`',
}

# permissions
admin_commands = ['1984start', '1984stop', '1984channel', '1984blacklist']
user_commands = ['1984report', '1984help']


