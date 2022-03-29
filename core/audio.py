import logging
import os.path
from pathlib import Path
from dataclasses import dataclass

from pyaudio import PyAudio, Stream, paInt16
# noinspection PyProtectedMember
from discord.opus import _load_default as opus_load_default, is_loaded as opus_is_loaded, load_opus


# Dataclasses to store PyAudio information in.
from core.exceptions import NoSuchAudioDevice


@dataclass()
class PyAudioHostAPI:
    index: int
    name: str
    device_count: int


@dataclass()
class PyAudioDevice:
    index: int
    name: str
    host_api: PyAudioHostAPI
    default_sample_rate: int


log = logging.getLogger(__name__)
audio = PyAudio()

# Globals that contain cached audio APIs and devices.
host_api_index_to_name: dict[int, PyAudioHostAPI] = {}
device_index_to_device: dict[int, PyAudioDevice] = {}


def open_input_device(
        device_name: str,
        with_sample_rate: int = 48000,
        with_host_api_name: str = "Windows WASAPI"
) -> tuple[Stream, int]:
    """
    Open an input device's Stream.

    :param device_name: Input device name to open.
    :param with_sample_rate: Sample rate to open the device with.
    :param with_host_api_name: Host API (name) to use.
    :return: PyAudio input (Stream) and frames per buffer (int) tuple.
    """
    matching_devices: list[PyAudioDevice] = [
        d for d in device_index_to_device.values()
        if d.name == device_name and d.default_sample_rate == with_sample_rate and d.host_api.name == with_host_api_name
    ]
    if len(matching_devices) < 1:
        raise NoSuchAudioDevice("No device with such name.")

    device: PyAudioDevice = matching_devices[0]

    frames_per_buffer: int = int(device.default_sample_rate * 0.02)

    return (
        audio.open(
            format=paInt16,
            channels=2,
            rate=device.default_sample_rate,
            input=True,
            input_device_index=device.index,
            frames_per_buffer=frames_per_buffer,
        ),
        frames_per_buffer
    )


def ensure_opus():
    """
    This helper function attempts to load the default opus library (if installed),
    falling back to "libs/opus.dll" if the first attempt fails (especially useful in packaged versions of the bot).
    """
    opus_load_default()

    if not opus_is_loaded():
        opus_dll_path = (Path(os.path.dirname(__file__)) / "libs/libopus-0.x64.dll").resolve()
        load_opus(str(opus_dll_path))

    print(f"Opus is loaded: {opus_is_loaded()}")


def setup():
    """
    This function gets and caches the host audio APIs and devices.
    """
    global host_api_index_to_name
    global device_index_to_device

    # Enumerate all host audio APIs
    api_count: int = audio.get_host_api_count()
    for api_index in range(api_count):
        api_info: dict = audio.get_host_api_info_by_index(api_index)

        api_name: str = api_info.get("name")
        if api_name is None:
            continue

        api_device_count: int = api_info.get("deviceCount")
        if not api_device_count:
            continue

        host_api: PyAudioHostAPI = PyAudioHostAPI(
            index=api_index,
            name=api_name,
            device_count=api_device_count
        )

        host_api_index_to_name[api_index] = host_api

    log.info(f"Enumerated {len(host_api_index_to_name)} host audio APIs.")

    # Enumerate all host audio devices
    devices_count: int = audio.get_device_count()
    for device_index in range(devices_count):
        device_info: dict = audio.get_device_info_by_index(device_index)

        device_name: str = device_info.get("name")
        if device_name is None:
            continue
        device_sample_rate: float = device_info.get("defaultSampleRate")
        if device_sample_rate is None:
            continue
        device_host_api_index: int = device_info.get("hostApi", -1)
        if device_host_api_index is None:
            continue

        device_host_api: PyAudioHostAPI = host_api_index_to_name[device_host_api_index]

        device: PyAudioDevice = PyAudioDevice(
            index=device_index,
            name=device_name,
            host_api=device_host_api,
            default_sample_rate=int(device_sample_rate)
        )

        device_index_to_device[device_index] = device

    log.info(f"Enumerated {len(device_index_to_device)} host audio devices.")


setup()
