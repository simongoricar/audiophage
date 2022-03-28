import logging
logging.basicConfig(level=logging.INFO)

from typing import Optional

from discord import Intents, Interaction, Guild, VoiceChannel, VoiceClient, AudioSource
from discord.abc import GuildChannel
from discord.enums import ChannelType
from discord.app_commands import CommandTree
from discord.ext.commands import Bot, Context
# noinspection PyProtectedMember
from discord.opus import _load_default as opus_load_default, is_loaded as opus_is_loaded

from core.audio import open_input_device
from core.configuration import config

log = logging.getLogger(__name__)

intents = Intents.all()
client = Bot(intents=intents, command_prefix=">")

opus_load_default()
print(f"Opus is loaded: {opus_is_loaded()}")

class MicAudioSource(AudioSource):
    def __init__(self):
        _stream, _frames_per_buffer = open_input_device(
            config.AUDIO_INPUT_DEVICE_NAME,
            config.AUDIO_INPUT_SAMPLE_RATE,
            config.AUDIO_HOST_API_NAME,
        )

        self._stream = _stream
        self._frames_per_buffer = _frames_per_buffer
        log.info(f"MicAudioSource frames per buffer: {self._frames_per_buffer}")

        self._is_closed: bool = False

    def read(self) -> bytes:
        if self._is_closed:
            return bytes(self._frames_per_buffer)

        # noinspection PyTypeChecker
        return self._stream.read(self._frames_per_buffer)

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        self._is_closed = True
        self._stream.stop_stream()
        self._stream.close()


# Event listeners
@client.event
async def on_ready():
    log.info(f"Logged in as bot {client.user.name}#{client.user.discriminator} ({client.user.id}).")
    log.info(f"Command prefix is \"{client.command_prefix}\".")


# Tree commands
@client.command(name="ping")
async def cmd_ping(ctx: Context):
    await ctx.reply("Pong!")


@client.command(name="join")
async def cmd_join(ctx: Context):
    reply = await ctx.reply("Joining.")

    join_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)
    join_voice_channel: GuildChannel = join_guild.get_channel(config.AUTO_JOIN_VOICE_CHANNEL_ID)
    if join_voice_channel.type != ChannelType.voice:
        await reply.edit(content="Can't join: not a voice channel!")
        return
    join_voice_channel: VoiceChannel

    voice_client: VoiceClient = await join_voice_channel.connect()
    mic = MicAudioSource()

    voice_client.play(mic)

@client.command(name="leave")
async def cmd_leave(ctx: Context):
    join_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)

    voice_client: Optional[VoiceClient] = join_guild.voice_client
    if voice_client is None:
        await ctx.reply("Not connected.")
    else:
        reply = await ctx.reply("Leaving.")

        # noinspection PyTypeChecker
        mic_source: MicAudioSource = voice_client.source
        if mic_source is None:
            await reply.edit(content="Something went wrong.")
            await voice_client.disconnect(force=True)
        else:
            voice_client.stop()
            mic_source.cleanup()
            await voice_client.disconnect()


def main():
    log.info("Starting bot ...")
    client.run(config.BOT_TOKEN)

if __name__ == '__main__':
    main()
