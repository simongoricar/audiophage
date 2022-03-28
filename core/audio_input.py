import logging
import traceback
from typing import Optional

from discord import AudioSource
from pyaudio import Stream

from .audio import open_input_device

log = logging.getLogger(__name__)


class PyAudioInputSource(AudioSource):
    """
    A discord AudioSource that takes and streams a PyAudio stream.
    """
    __slots__ = ("_stream", "_frames_per_buffer", "_is_closed")

    def __init__(self, stream: Stream, frames_per_buffer: int):
        """
        Given a PyAudio (input) Stream and the amount of frames per buffer the Stream was configured with,
        create a new PyAudioInputSource that can be passed over to VoiceClient.play.
        NOTE: Discord.py requires 16-bit 48 kHz stereo PCM.

        :param stream: AudioPy Stream.
        :param frames_per_buffer: Amount of frames per buffer that will be read each iteration.
                                  Discord.py requests this is equal to 20ms of audio, which means (at 48 kHz):
                                  48000 * 0.02 = 960 frames.
        """
        log.debug(f"New PyAudioInputSource: {frames_per_buffer=}.")

        # A few checks to make sure we can actually use this Stream instead of just silently failing.
        if not stream.is_active():
            stream.start_stream()
            if not stream.is_active():
                raise RuntimeError("Can't start audio stream!")

        self._stream = stream
        self._frames_per_buffer = frames_per_buffer

        self._is_closed: bool = False

    @classmethod
    def create(cls, device_name: str, host_api_name: str) -> Optional["PyAudioInputSource"]:
        """
        Open an input device and instantiate a new PyAudioInputSource.

        :param device_name: Device to open by name (see list-audio-info.py for available APIs and devices).
        :param host_api_name: Host audio API to use by name (see list-audio-info.py for available APIs and devices).
        :return: PyAudioInputSource instance that can be passed over to VoiceClient.play.
        """
        _stream, _frames_per_buffer = open_input_device(
            device_name,
            48000,
            host_api_name,
        )

        try:
            return cls(_stream, _frames_per_buffer)
        except RuntimeError as err:
            log.error(f"Couldn't instantiate PyAudioInputSource: {err}")
            traceback.print_exc()

            _stream.stop_stream()
            _stream.close()

    def read(self) -> bytes:
        """
        Read 20ms worth of audio. The length of the bytes returned will be:
        frames * 2 (stereo) * 2 (16 bits) = 3840
        """
        if self._is_closed:
            return bytes(self._frames_per_buffer * 2 * 2)

        # noinspection PyTypeChecker
        return self._stream.read(self._frames_per_buffer)

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        self._is_closed = True

        try:
            self._stream.stop_stream()
            self._stream.close()
        except AttributeError:
            pass
