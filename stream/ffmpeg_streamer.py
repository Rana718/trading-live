import subprocess
import numpy as np
from PIL import Image
from config import WIDTH, HEIGHT, FPS, YOUTUBE_RTMP_URL, YOUTUBE_STREAM_KEY


def _build_ffmpeg_cmd() -> list[str]:
    rtmp_target = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"
    return [
        "ffmpeg", "-y",
        # video input: raw RGB frames from stdin
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
        "-r", str(FPS), "-i", "pipe:0",
        # audio input: silent (VOICEVOX audio mixed separately via pipe:3)
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        # encode
        "-vcodec", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
        "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
        "-acodec", "aac", "-ar", "44100", "-b:a", "128k",
        "-f", "flv", rtmp_target,
    ]


class FFmpegStreamer:
    def __init__(self):
        self._proc: subprocess.Popen | None = None

    def start(self):
        self._proc = subprocess.Popen(
            _build_ffmpeg_cmd(),
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

    def send_frame(self, img: Image.Image):
        if self._proc and self._proc.stdin:
            self._proc.stdin.write(np.array(img.resize((WIDTH, HEIGHT))).tobytes())

    def stop(self):
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
            self._proc = None

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
