from pathlib import Path
from typing import Optional, Dict, List

from .configuration_base import TOMLConfig


def get_str_to_str_dict(table: TOMLConfig, key: str) -> Dict[str, str]:
    """
    Given a TOMLConfig table and a key, return a dict[str, str] on that key.
    """
    return {
        str(k): str(v) for k, v in table.get(key, {}).items()
    }


def get_int_to_str_dict(table: TOMLConfig, key: str) -> Dict[int, str]:
    """
    Given a TOMLConfig table and a key, return a dict[int, str] on that key.
    """
    return {
        int(k): str(v) for k, v in table.get(key, {}).items()
    }


def get_str_list(table: "TOMLConfig", key: str) -> List[str]:
    """
    Given a table and a key, retrieve the configuration value at that key and ensure it is a list[str].

    :param table: TOMLConfig table instance.
    :param key: Key to retrieve value for.
    :return: A list of strings at the specified configuration key.
    """
    configuration_value = table.get(key)
    if configuration_value is None:
        raise TypeError(f"Missing configuration value: {key}")

    if not isinstance(configuration_value, list):
        raise TypeError(f"{key} was expected to be list[str], got {type(configuration_value)}")

    return [str(value) for value in configuration_value]


def get_str_with_placeholders(
        table: "TOMLConfig",
        key: str,
        placeholders: Dict[str, str] = None,
        allow_empty: bool = False,
) -> Optional[str]:
    """
    Given a table, a key and a dictionary containing placeholder values to replace,
    retrieve the configuration value, clean up the leading/trailing whitespace and replace the placeholder values.

    :param table: TOMLConfig table instance.
    :param key: Key to retrieve value for.
    :param placeholders: A dict containing keys as the placeholders to replace.
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
            raise TypeError(f"Missing configuration value: {key}")

    if not isinstance(configuration_value, str):
        raise TypeError(
            f"Expected configuration value at {key} to be str, but got {type(configuration_value)}"
        )

    if configuration_value.strip(" ") == "":
        if allow_empty:
            return None
        else:
            raise TypeError(f"Value at {key} is empty (only whitespace).")

    # Clean up the string
    configuration_value = configuration_value.strip(" ")
    # Replace placeholder values
    if placeholders is not None:
        for key, value in placeholders.items():
            configuration_value = configuration_value.replace("{" + key + "}", value)

    return configuration_value


def get_optional_path_from_str(path_string: Optional[str], resolve: bool = True) -> Optional[Path]:
    """
    Convert a string path into a Path instance and resolve it to an absolute path.

    :param path_string: Path string to convert.
    :param resolve: Whether to resolve the path to an absolute one.
    :return: Path instance or None (if empty path string).
    """
    if path_string is None or path_string.strip() == "":
        return None
    else:
        if resolve:
            return Path(path_string).resolve()
        else:
            return Path(path_string)
