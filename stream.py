import logging
logging.basicConfig(level=logging.INFO)

import traceback
from typing import Optional, Literal

from discord import Intents, Guild, VoiceChannel, VoiceClient, \
    Client, Object, Interaction, Member, User
from discord.abc import GuildChannel
from discord.app_commands import CommandTree, describe, check
from discord.enums import ChannelType

from core.audio_input import PyAudioInputSource
from core.configuration import config
from core.emojis import Emoji
from core.state import AudiophageState
from core.exceptions import NotConnected, AudioException, NoSuchAudioDevice

log = logging.getLogger(__name__)

intents = Intents.all()
client = Client(intents=intents)
tree = CommandTree(client)
state = AudiophageState()

if len(config.GUILD_IDS) == 0:
    log.error("The configuration value permissions.guild_ids does not contain any guild IDs. "
              "This effectively means the bot will work nowhere. Please add at least one guild "
              "you want to use the bot on in configuration.toml.")
valid_guilds: list[Object] = [Object(id=i) for i in config.GUILD_IDS]

if len(config.USER_IDS) == 0:
    log.error("The configuration value permissions.user_ids does not contain any user IDs. "
              "This effectively means the bot will not respond to anyone. Please add at least one "
              "user you want to operate the bot.")


##
# Utilities
##
async def get_primary_voice_channel() -> Optional[VoiceChannel]:
    """
    Get the primary (auto-joinable) VoiceChannel based on the configuration
    (see subtable "auto_join" in configuration.toml).
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

async def connect_and_stream(voice_channel: VoiceChannel) -> VoiceClient:
    """
    Connect to a VoiceChannel and start streaming the configured input device.

    :param voice_channel: VoiceChannel to connect and stream to.
    :return: VoiceClient
    """
    input_source = PyAudioInputSource.create(
        config.AUDIO_INPUT_DEVICE_NAME,
        config.AUDIO_HOST_API_NAME,
    )

    voice_client: VoiceClient = await voice_channel.connect()

    voice_client.play(input_source)
    state.set_stream_started(voice_client)

    return voice_client

async def stop_stream_and_disconnect() -> VoiceChannel:
    """
    Disconnect from the current audio stream (if connected) and leave the voice channel.

    :return: VoiceChannel we just disconnected from.
    """
    voice_client: Optional[VoiceClient] = state.stream
    if voice_client is None:
        raise NotConnected()

    voice_channel: VoiceChannel = voice_client.channel

    voice_client.stop()
    await voice_client.disconnect()

    state.set_stream_ended()

    return voice_channel


def is_whitelisted_user(interaction: Interaction):
    """
    A callback to check whether the user that initiated the Interaction is whitelisted.
    """
    user: User = interaction.user
    return user.id in config.USER_IDS


##
# Event listeners
##
@client.event
async def on_ready():
    log.info(f"Logged in as bot {client.user.name}#{client.user.discriminator} ({client.user.id}).")

    # Sync global and guild slash commands.
    log.info(f"Syncing global slash commands.")
    await tree.sync()

    for guild_id in config.GUILD_IDS:
        guild: Guild = client.get_guild(guild_id)
        if guild is not None:
            log.info(f"Syncing slash commands for guild: {guild.name} ({guild.id}).")
            await tree.sync(guild=guild)

    # List whitelisted user info
    whitelisted_users: list[User] = [client.get_user(i) for i in config.USER_IDS]
    whitelisted_names: list[str] = [f"{u.name}#{u.discriminator}:{u.id}" for u in whitelisted_users if u is not None]
    log.info(f"Whitelisted users: {', '.join(whitelisted_names)}")

    # Perform an auto-join if configured to do so.
    if config.AUTO_JOIN_ENABLED:
        primary_voice: Optional[VoiceChannel] = await get_primary_voice_channel()
        if primary_voice is None:
            log.warning(f"Auto-join was enabled, but can't find voice channel!")
            return

        log.info(f"Auto-join is enabled! Joining {primary_voice}!")

        try:
            await connect_and_stream(primary_voice)
        except AudioException as err:
            log.error(f"Couldn't auto-join, audio error: {err}")
            traceback.print_exc()

        log.info(f"Auto-joined!")


##
# Bot commands
##
@tree.command(
    name="ping",
    description="Request a simple pong response from the bot to confirm it is running.",
    guilds=valid_guilds
)
async def cmd_ping(interaction: Interaction):
    log.info(f"User {interaction.user} requested: ping")
    await interaction.response.send_message(f"{Emoji.PING_PONG} Pong!", ephemeral=True)


@tree.command(
    name="join",
    description="Join either the caller or the main (also called auto-join) channel and begin streaming.",
    guilds=valid_guilds,
)
@describe(
    where="\"me\" - voice channel you're currently in, \"primary\" - the auto-join-configured channel."
)
@check(is_whitelisted_user)
async def cmd_join(interaction: Interaction, where: Literal["me", "primary"]):
    log.info(f"User {interaction.user} requested: join.")

    already_streaming: bool = state.stream is not None
    if already_streaming:
        log.info("Can't join: already streaming somewhere else.")
        await interaction.response.send_message(
            f"{Emoji.WARNING} Can't join: already streaming somewhere else - only a single stream is supported."
        )
        return

    voice_channel: Optional[VoiceChannel]
    if where == "primary":
        voice_channel = await get_primary_voice_channel()
        if voice_channel is None:
            log.info("Can't join primary channel: not a voice channel!")
            await interaction.response.send_message(
                f"{Emoji.WARNING} Can't join primary channel: not a voice channel!",
                ephemeral=True
            )
            return

    elif where == "me":
        voice_channel = find_user_voice_channel(interaction.user)
        if voice_channel is None:
            log.info(f"Can't join {interaction.user}, not in a voice channel.")
            await interaction.response.send_message(f"{Emoji.WARNING} Can't join: you're not in any voice channel!",
                                                    ephemeral=True)
            return

    else:
        await interaction.response.send_message(
            f"{Emoji.WARNING} Not a valid argument (expected either `me` or `main`)!",
            ephemeral=True
        )
        return

    try:
        await connect_and_stream(voice_channel)
        log.info(f"Voice channel joined and streaming: {voice_channel} ({voice_channel.id}).")
        await interaction.response.send_message(f"{Emoji.POSTAL_HORN} Joined voice channel: {voice_channel.mention}.",
                                                ephemeral=True)

    except AudioException as err:
        log.error(f"Couldn't join voice channel, audio error: {err}")
        traceback.print_exc()
        await interaction.response.send_message(content=f"{Emoji.EYES} Error while opening input audio stream!",
                                                ephemeral=True)

    except NoSuchAudioDevice:
        log.error("Couldn't open stream: the configured audio device does not exist.")
        await interaction.response.send_message(content=f"{Emoji.EYES} The configured audio input device does not exist"
                                                        f" (disconnected or otherwise unavailable)!",
                                                ephemeral=True)


@tree.command(
    name="leave",
    description="Stop streaming and leave the voice channel.",
    guilds=valid_guilds,
)
@check(is_whitelisted_user)
async def cmd_leave(interaction: Interaction):
    log.info(f"User {interaction.user} requested: leave.")

    try:
        voice_channel: VoiceChannel = await stop_stream_and_disconnect()

    except NotConnected:
        log.info("Can't leave: not connected.")
        await interaction.response.send_message(f"{Emoji.WARNING} Can't leave: not connected.", ephemeral=True)

    else:
        log.info(f"Stopped streaming and left {voice_channel.name} ({voice_channel.id}).")
        await interaction.response.send_message(
            f"{Emoji.WAVE} Leaving {voice_channel.mention}.", ephemeral=True
        )


def main():
    log.info("Starting bot ...")
    client.run(config.BOT_TOKEN)

if __name__ == '__main__':
    main()
