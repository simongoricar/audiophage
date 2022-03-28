import logging
logging.basicConfig(level=logging.INFO)

from typing import Optional, Literal

from discord import Intents, Guild, VoiceChannel, VoiceClient, Client, Object, Interaction, Member, User
from discord.abc import GuildChannel
from discord.app_commands import CommandTree
from discord.enums import ChannelType

from core.audio_input import PyAudioInputSource
from core.configuration import config
from core.emojis import Emoji
from core.context import Context

log = logging.getLogger(__name__)

intents = Intents.all()
client = Client(intents=intents)
tree = CommandTree(client)
context = Context()

main_guild_obj: Object = Object(id=config.MAIN_GUILD_ID)

##
# Utilities
##
async def get_autojoin_voice_channel() -> Optional[VoiceChannel]:
    """
    Get the auto-join VoiceChannel based on the configuration.
    """
    autojoin_guild: Guild = client.get_guild(config.AUTO_JOIN_GUILD_ID)

    join_voice_channel: GuildChannel = autojoin_guild.get_channel(config.AUTO_JOIN_VOICE_CHANNEL_ID)
    if join_voice_channel.type != ChannelType.voice:
        return None

    join_voice_channel: VoiceChannel
    return join_voice_channel

def find_user_voice_channel(user: User) -> Optional[VoiceChannel]:
    mutual_guilds: list[Guild] = user.mutual_guilds

    for guild in mutual_guilds:
        member: Member = guild.get_member(user.id)
        if member.voice is not None and member.voice.channel is not None:
            if member.voice.channel.type == ChannelType.voice:
                return member.voice.channel
            else:
                # Could be a stage channel, which doesn't qualify.
                return None

    return None


##
# Event listeners
##
@client.event
async def on_ready():
    log.info(f"Logged in as bot {client.user.name}#{client.user.discriminator} ({client.user.id}).")

    log.info(f"Syncing global slash commands.")
    await tree.sync()

    main_guild: Guild = client.get_guild(config.MAIN_GUILD_ID)
    log.info(f"Syncing slash commands for main guild: {main_guild}.")
    await tree.sync(guild=main_guild)

    if config.AUTO_JOIN_ENABLED:
        autojoin_channel: Optional[VoiceChannel] = await get_autojoin_voice_channel()
        if autojoin_channel is None:
            log.warning(f"Auto-join was enabled, but can't find voice channel!")
            return

        log.info(f"Auto-join is enabled, joining {autojoin_channel}!")

        voice_client: VoiceClient = await autojoin_channel.connect()

        mic = PyAudioInputSource.create(
            config.AUDIO_INPUT_DEVICE_NAME,
            config.AUDIO_HOST_API_NAME,
        )

        if mic is None:
            await voice_client.disconnect()
            return

        voice_client.play(mic)

        context.set("is_streaming", True)
        context.set("stream_client", voice_client)

        log.info(f"Auto-join done!")


##
# Bot commands
##
@tree.command(
    name="ping",
    description="Request a simple pong response from the bot to confirm it is running.",
    guild=main_guild_obj
)
async def cmd_ping(interaction: Interaction):
    await interaction.response.send_message(f"{Emoji.PING_PONG} Pong!", ephemeral=True)


@tree.command(
    name="join",
    description="Join either the caller or the main (also called auto-join) channel.",
    guild=main_guild_obj,
)
async def cmd_join(interaction: Interaction, what: Literal["me", "main"]):
    log.info(f"User {interaction.user} requested: join.")

    is_streaming: bool = bool(context.get("is_streaming", default=False))
    if is_streaming:
        await interaction.response.send_message(
            f"{Emoji.WARNING} Can't join: already streaming."
        )
        return

    voice_channel: Optional[VoiceChannel]
    if what == "main":
        voice_channel = await get_autojoin_voice_channel()
        if voice_channel is None:
            await interaction.response.send_message(
                f"{Emoji.WARNING} Can't join auto-join channel: not a voice channel!", ephemeral=True
            )
            return

    elif what == "me":
        voice_channel = find_user_voice_channel(interaction.user)
        if voice_channel is None:
            await interaction.response.send_message(
                f"{Emoji.WARNING} Can't join: you're not in a voice channel!", ephemeral=True
            )
            return

    else:
        await interaction.response.send_message(
           f"{Emoji.WARNING} Not a valid argument (expected either `me` or `main`)!", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"{Emoji.POSTAL_HORN} Joining voice channel: {voice_channel.mention}.", ephemeral=True
    )
    voice_client: VoiceClient = await voice_channel.connect()

    mic = PyAudioInputSource.create(
        config.AUDIO_INPUT_DEVICE_NAME,
        config.AUDIO_HOST_API_NAME,
    )
    if mic is None:
        await interaction.response.edit_message(content=f"{Emoji.EYES} Can't open audio input stream!")
        await voice_client.disconnect()
        return

    voice_client.play(mic)

    context.set("is_streaming", True)
    context.set("stream_client", voice_client)


@tree.command(
    name="leave",
    description="Leave the current voice channel.",
    guild=main_guild_obj,
)
async def cmd_leave(interaction: Interaction):
    log.info(f"User {interaction.user} requested: leave.")

    def reset_streaming():
        context.set("is_streaming", False)
        context.set("stream_client", None)

    is_streaming: bool = bool(context.get("is_streaming", default=False))
    if not is_streaming:
        await interaction.response.send_message(f"{Emoji.WARNING} Can't leave: not connected.", ephemeral=True)
        reset_streaming()
        return

    voice_client: Optional[VoiceClient] = context.get("stream_client", default=None)
    if not voice_client:
        await interaction.response.send_message(f"{Emoji.EYES} You just found an edge case! "
                                                f"Streaming somewhere, but voice client is None!")
        reset_streaming()
        return

    # noinspection PyTypeChecker
    mic_source: PyAudioInputSource = voice_client.source
    if not isinstance(mic_source, PyAudioInputSource):
        await interaction.response.send_message(f"{Emoji.EYES} You just found an edge case! "
                                                f"VoiceClient source is not a PyAudioInputSource for some reason! "
                                                f"Forcing disconnect, this is a bug.")
        await voice_client.disconnect(force=True)
        reset_streaming()
        return

    # Normal disconnect.
    await interaction.response.send_message(
        f"{Emoji.WAVE} Leaving {voice_client.channel.mention}.", ephemeral=True
    )

    voice_client.stop()
    await voice_client.disconnect()

    reset_streaming()


def main():
    log.info("Starting bot ...")
    client.run(config.BOT_TOKEN)

if __name__ == '__main__':
    main()
