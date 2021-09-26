import os, subprocess

class SoundNotification:
    def __init__(self):
        home_dir = os.path.expanduser('~')
        self._dir = f"{home_dir}/sounds"

    def info(self):
        self._play("notify.wav")

    def error(self):
        self._play("chord.wav")

    def ding(self):
        self._play("ding.wav")

    def _play(self, name: str):
        args = ["paplay", f"{self._dir}/{name}"]
        subprocess.Popen(args, close_fds=True, stderr=subprocess.STDOUT, stdout=subprocess.DEVNULL)
