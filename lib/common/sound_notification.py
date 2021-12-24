import os, subprocess, gtts

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


class VoiceNotification:
    @staticmethod
    def say(text: str):
        r,w = os.pipe()
        o = gtts.gTTS(text=text, lang="en", slow=False)
        subprocess.Popen(["mpg123", "-"], close_fds=False, stderr=subprocess.STDOUT, stdout=subprocess.DEVNULL, stdin=os.fdopen(r, mode="rb"))
        w = os.fdopen(w,mode="wb")
        o.write_to_fp(w)
        w.close()
