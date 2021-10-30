
class StatusBar:

    def __init__(self, count: int, width_chars: int):
        self._count = count
        self._width = width_chars

    def progress(self, pos: int):
        fill = "#"
        space = "."
        fill_chars = int(pos / self._count * self._width)
        print("\rloading [", end="", flush=False)
        print(fill * fill_chars, end="", flush=False)
        print(space * (self._width - fill_chars), end="", flush=False)
        print("]", end="", flush=True)

    def clear(self):
        print("\r         " +  " " * (self._width + 2) + "\r", end="", flush=True)

