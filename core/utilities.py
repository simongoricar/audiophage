from typing import Union


def clamp(value: Union[int, float], min_: Union[int, float], max_: Union[int, float]) -> Union[int, float]:
    if value < min_:
        return min_
    elif value > max_:
        return max_
    else:
        return value
