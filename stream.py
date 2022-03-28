import logging
logging.basicConfig(level=logging.INFO)

from typing import Optional

from discord import Intents, Client, Interaction, Guild, VoiceChannel, VoiceClient, AudioSource
from discord.abc import GuildChannel
from discord.enums import ChannelType
from discord.app_commands import CommandTree
from discord.ext.commands import Bot
# noinspection PyProtectedMember
from discord.opus import _load_default as opus_load_default, is_loaded as opus_is_loaded

from core.audio import open_input_device
from core.configuration import config

log = logging.getLogger(__name__)

intents = Intents.all()
client = Bot(intents=intents)
tree = CommandTree(client)

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

        self._is_closed: bool = False

    def read(self) -> bytes:
        if self._is_closed:
            return bytes(self._frames_per_buffer)

        result = self._stream.read(self._frames_per_buffer)
        print(f"Read data, is type {type(result)} and size {len(result)}")
        # noinspection PyTypeChecker
        return result

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        self._is_closed = True
        self._stream.close()


# Event listeners
@client.event
async def on_ready():
    log.info(f"Logged in as bot {client.user.name}#{client.user.discriminator} ({client.user.id}).")

    main_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)
    log.info(f"Syncing slash commands with main guild: {main_guild}.")
    await tree.sync(guild=main_guild)
    log.info(f"Commands synced.")


# Tree commands
@tree.command(
    name="ping",
    description="Ping the bot."
)
async def cmd_ping(interaction: Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)


@tree.command(
    name="join",
    description="Join the voice channel and stream microphone audio."
)
async def cmd_join(interaction: Interaction):
    await interaction.response.send_message("Joining.", ephemeral=True)

    join_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)
    join_voice_channel: GuildChannel = join_guild.get_channel(config.AUTO_JOIN_VOICE_CHANNEL_ID)
    if join_voice_channel.type != ChannelType.voice:
        await interaction.response.edit_message(content="Can't join: not a voice channel!")
        return
    join_voice_channel: VoiceChannel

    voice_client: VoiceClient = await join_voice_channel.connect()
    mic = MicAudioSource()

    voice_client.play(mic)

@tree.command(
    name="leave",
    description="Stop streaming microphone audio and leave the voice channel."
)
async def cmd_leave(interaction: Interaction):
    join_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)

    voice_client: Optional[VoiceClient] = join_guild.voice_client
    if voice_client is None:
        await interaction.response.send_message("Not connected.", ephemeral=True)
    else:
        await interaction.response.send_message("Leaving.", ephemeral=True)

        # noinspection PyTypeChecker
        mic_source: MicAudioSource = voice_client.source
        if mic_source is None:
            await interaction.response.edit_message(content="Something went wrong.")
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
