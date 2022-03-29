from typing import Optional

from discord import VoiceClient

class AudiophageState:
    """
    A simple key-value store in the form of a class.
    """
    __slots__ = ("_is_streaming", "_voice_client")

    def __init__(self):
        self._is_streaming: bool = False
        self._voice_client: Optional[VoiceClient] = None

    def set_stream_started(self, client: VoiceClient):
        self._is_streaming = True
        self._voice_client = client

    def set_stream_ended(self):
        self._is_streaming = False
        self._voice_client = None

    @property
    def stream(self) -> Optional[VoiceClient]:
        return self._voice_client if self._is_streaming else None
