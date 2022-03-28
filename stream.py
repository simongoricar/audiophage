import logging
logging.basicConfig(level=logging.INFO)

from typing import Optional

from discord import Intents, Guild, VoiceChannel, VoiceClient
from discord.abc import GuildChannel
from discord.enums import ChannelType
from discord.ext.commands import Bot, Context

from core.audio_input import PyAudioInputSource
from core.configuration import config

log = logging.getLogger(__name__)

intents = Intents.all()
client = Bot(intents=intents, command_prefix=">")

##
# Event listeners
##
@client.event
async def on_ready():
    log.info(f"Logged in as bot {client.user.name}#{client.user.discriminator} ({client.user.id}).")
    log.info(f"Bot command prefix is \"{client.command_prefix}\".")


##
# Bot commands
##
@client.command(name="ping")
async def cmd_ping(ctx: Context):
    await ctx.reply("Pong!")


@client.command(name="join")
async def cmd_join(ctx: Context):
    log.info(f"User {ctx.author} requested: join.")

    reply = await ctx.reply("Joining.")

    join_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)
    join_voice_channel: GuildChannel = join_guild.get_channel(config.AUTO_JOIN_VOICE_CHANNEL_ID)
    if join_voice_channel.type != ChannelType.voice:
        await reply.edit(content="Can't join: not a voice channel!")
        return
    join_voice_channel: VoiceChannel

    voice_client: VoiceClient = await join_voice_channel.connect()
    mic = PyAudioInputSource.create(
        config.AUDIO_INPUT_DEVICE_NAME,
        config.AUDIO_HOST_API_NAME,
    )

    voice_client.play(mic)

@client.command(name="leave")
async def cmd_leave(ctx: Context):
    log.info(f"User {ctx.author} requested: leave.")

    join_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)

    voice_client: Optional[VoiceClient] = join_guild.voice_client
    if voice_client is None:
        await ctx.reply("Not connected.")
    else:
        reply = await ctx.reply("Leaving.")

        # noinspection PyTypeChecker
        mic_source: PyAudioInputSource = voice_client.source
        if mic_source is None:
            await reply.edit(content="Something went wrong.")
            await voice_client.disconnect(force=True)
        else:
            voice_client.stop()
            await voice_client.disconnect()
            mic_source.cleanup()


def main():
    log.info("Starting bot ...")
    client.run(config.BOT_TOKEN)

if __name__ == '__main__':
    main()
