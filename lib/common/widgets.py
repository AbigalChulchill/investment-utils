from typing import Any
from collections.abc import Iterable

def simple_progress_track(sequence: Iterable[Any], with_item_text: bool = True) -> Iterable[Any]:
    n = len(sequence)
    i = 0
    text_pad = 0
    for x in sequence:
        i += 1
        if with_item_text:
            text_pad = max(text_pad, len(str(x)))
            item_text = f"....{str(x)}" + " "*text_pad
        else:
            item_text = ""
        print(f"{i / n * 100.:>3.0f}%  " + item_text, end="\r")
        yield x
