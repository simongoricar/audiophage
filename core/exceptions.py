class AudiophageException(Exception):
    """
    Base class for Audiophage-specific exceptions.
    """

class StreamException(AudiophageException):
    """
    General class for audio streaming-related problems.
    """

class NotConnected(StreamException):
    """
    Raised when trying to leave a stream that doesn't exist.
    """

class AudioException(AudiophageException):
    """
    General class for audio-related exceptions.
    """

class NoSuchAudioDevice(AudiophageException):
    """
    Raised when the requested audio device does not exist (is not connected or otherwise).
    """
