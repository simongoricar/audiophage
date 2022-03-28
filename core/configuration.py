import logging
from pathlib import Path
from typing import Union, Optional

from .configuration_base import TOMLConfig, DATA_DIR

log = logging.getLogger(__name__)


class Configuration:
    def __init__(self, configuration: TOMLConfig):
        self._config: TOMLConfig = configuration

        ### Tables
        self._discord: TOMLConfig = self._config.get_table("discord", raise_on_missing_key=True)
        self._auto_join: TOMLConfig = self._config.get_table("auto_join", raise_on_missing_key=True)
        self._audio: TOMLConfig = self._config.get_table("audio", raise_on_missing_key=True)

        ## "discord" table
        self.BOT_TOKEN: str = self._discord.get("token", raise_on_missing_key=True)

        ## "auto_join" table
        self.AUTO_JOIN_ENABLED: bool = bool(self._auto_join.get("enabled", fallback=False))
        self.AUTO_JOIN_GUILD_ID: Optional[int] = self._auto_join.get("guild_id", fallback=None)
        self.AUTO_JOIN_VOICE_CHANNEL_ID: Optional[int] = self._auto_join.get("voice_channel_id", fallback=None)

        ## "audio" table
        self.AUDIO_HOST_API_NAME: str = self._audio.get("host_api_name", fallback="Windows WASAPI")
        self.AUDIO_INPUT_SAMPLE_RATE: int = int(self._audio.get("input_sample_rate", fallback=48000))
        self.AUDIO_INPUT_DEVICE_NAME: str = self._audio.get("input_device_name", raise_on_missing_key=True)

    @classmethod
    def from_file_path(cls, configuration_filepath: Union[str, Path]) -> "Configuration":
        """
        Initialize a new instance by reading from the specified configuration file.

        :param configuration_filepath: File path of the config file to read from.
        :return: Configuration instance with the parsed values.
        """
        return cls(TOMLConfig.from_filename(str(configuration_filepath)))


config_path = DATA_DIR / "configuration.toml"
config_template_path = DATA_DIR / "configuration.TEMPLATE.toml"

if not config_path.exists() and config_template_path.exists():
    raise RuntimeError(
        "Missing configuration.toml! Make sure to make a copy of configuration.TEMPLATE.toml and configure it."
    )

config = Configuration.from_file_path(config_path)
