from typing import Any


class Context:
    """
    A simple key-value store in the form of a class.
    """
    __slots__ = ("_store", )

    def __init__(self):
        self._store: dict[str, Any] = {}

    def set(self, key: str, value: Any, allow_existing: bool = True) -> None:
        if not allow_existing and key in self._store:
            raise KeyError(f"Key \"{key}\" already exists in context.")

        self._store[key] = value

    def get(self, key: str, default: Any = None, raise_on_missing: bool = False) -> Any:
        if raise_on_missing and key not in self._store:
            raise KeyError(f"Key \"{key}\" does not have a value in this context.")

        return self._store.get(key) or default
