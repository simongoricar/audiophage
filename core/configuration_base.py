"""
Handles entire configuration for the ZZRS Video Service project. Uses toml configuration files (with tomli).
"""

import os.path
from pathlib import Path
from typing import Any, Optional, Mapping, List

from tomli import load


# Points to the parent directory.
BASE_DIR = Path(os.path.dirname(__file__)).parent.resolve()
DATA_DIR = BASE_DIR / "data"

if not DATA_DIR.exists():
    raise FileNotFoundError("Missing directory: data!")


# Utility functions for parsing configuration values.
def _get_optional_path_from_string(path_string: Optional[str]) -> Optional[Path]:
    """
    Convert a string path into a Path instance and resolve it to an absolute path.

    :param path_string: Path string to convert.
    :return: Path instance or None (if empty path string).
    """
    if path_string is None or path_string.strip() == "":
        return None
    else:
        return Path(path_string).resolve()


def _get_value_with_placeholders(
        table: "TOMLConfig", key: str,
        placeholder_dict: dict = None,
        allow_empty: bool = False,
) -> Optional[str]:
    """
    Given a table, a key and a dictionary containing placeholder values to replace,
    retrieve the configuration value, clean up the leading/trailing whitespace and replace the placeholder values.

    :param table: TOMLConfig table instance.
    :param key: Key to retrieve value for.
    :param placeholder_dict: A dict containing keys as the placeholders to replace.
    Example: {"TEST": 123} will turn the original value "hello/{TEST}" into "hello/123".
    Useful for base paths and many dynamic values.
    :param allow_empty: Whether to simply return None ony missing (or empty) value.
    :return: A formatted and "clean" string (or possibly None if allow_empty=True).
    """
    configuration_value = table.get(key)

    if configuration_value is None:
        if allow_empty:
            return None
        else:
            raise ValueError(f"Missing configuration value: {key}")

    if not isinstance(configuration_value, str):
        raise ValueError(
            f"Expected configuration value at {key} to be str, but got {type(configuration_value)}"
        )

    if configuration_value.strip(" ") == "":
        if allow_empty:
            return None
        else:
            raise ValueError(f"Value at {key} is empty (only whitespace).")

    # Clean up the string
    configuration_value = configuration_value.strip(" ")

    # Replace placeholder values
    if placeholder_dict is not None:
        for key, value in placeholder_dict.items():
            configuration_value = configuration_value.replace("{" + key + "}", value)

    return configuration_value


def _get_str_list_value(table: "TOMLConfig", key: str) -> List[str]:
    """
    Given a table and a key, retrieve the configuration value at that key and ensure it is a list[str].

    :param table: TOMLConfig table instance.
    :param key: Key to retrieve value for.
    :return: A list of strings at the specified configuration key.
    """
    configuration_value = table.get(key)
    if configuration_value is None:
        raise ValueError(f"Missing configuration value: {key}")

    if not isinstance(configuration_value, list):
        raise ValueError(f"{key} was expected to be list[str], got {type(configuration_value)}")

    return [str(value) for value in configuration_value]


class TOMLConfig:
    """
    A minimal TOML file abstraction.
    Supports reading from a file and getting resulting values and subtables.

    See https://toml.io/en/ for more details.
    """
    __slots__ = ("data", )

    def __init__(self, json_data: Mapping):
        self.data = json_data

    @classmethod
    def from_filename(cls, file_path: str) -> "TOMLConfig":
        """
        Initialize a TOMLConfig instance by loading data from the specified file path.

        :param file_path: File path of the configuration file.
        :return: TOMLConfig instance with the configuration file loaded.
        :raises FileNotFoundError: If the specified file does not exist.
        """
        filepath = Path(file_path)
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file \"{filepath}\" does not exist.")

        with filepath.open(mode="rb") as config_file:
            data = load(config_file)

        return cls(data)

    def get_table(self, name: str, raise_on_missing_key: bool = False) -> Optional["TOMLConfig"]:
        """
        Get a sub-dict in the configuration (parsed into an instance of `TOMLConfig`).

        :param name: Key name.
        :param raise_on_missing_key: Whether to fall back to returning None when the key does not exist
        or to raise a ConfigurationException.
        :return: TOMLConfig instance with the dict value loaded,
        or None if the key does not exist (if raise_on_missing_key=False)
        """
        data = self.data.get(name)
        if data is None:
            if raise_on_missing_key:
                raise ValueError(f"Configuration table missing: '{name}'")
            else:
                return None

        return TOMLConfig(data)

    def get(self, name: str, fallback: Any = None, raise_on_missing_key: bool = False) -> Any:
        """
        Return a value associated with the configuration key.

        :param name: Key name.
        :param fallback: If raise_on_missing_key=False and the value at a specific key is None or does not exist,
        the fallback value will be returned and can be specified using this parameter.
        :param raise_on_missing_key: Whether to raise a ConfigurationException on missing configuration keys.
        :return: Value associated with the key or the fallback value (if no exception was raised).
        """
        data = self.data.get(name)
        if data is None and raise_on_missing_key:
            raise ValueError(f"Configuration value missing: '{name}'")
        elif data is None:
            return fallback
        else:
            return data
