import subprocess
import threading
import tempfile
import os
import numpy as np
from PIL import Image
from config import WIDTH, HEIGHT, FPS, YOUTUBE_RTMP_URL, YOUTUBE_STREAM_KEY


class FFmpegStreamer:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._audio_proc: subprocess.Popen | None = None
        self._fifo_path: str | None = None

    def start(self):
        # Create a named FIFO for audio
        self._fifo_path = tempfile.mktemp(suffix=".fifo")
        os.mkfifo(self._fifo_path)

        rtmp_target = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"

        # Main FFmpeg: video from stdin, audio from FIFO
        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y",
                # video
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
                "-r", str(FPS), "-i", "pipe:0",
                # audio from fifo
                "-f", "wav", "-i", self._fifo_path,
                # encode
                "-vcodec", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
                "-acodec", "aac", "-ar", "44100", "-b:a", "128k",
                "-shortest", "-f", "flv", rtmp_target,
            ],
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

    def send_frame(self, img: Image.Image):
        if self._proc and self._proc.stdin:
            try:
                self._proc.stdin.write(np.array(img.resize((WIDTH, HEIGHT))).tobytes())
            except BrokenPipeError:
                pass

    def play_audio(self, wav_bytes: bytes):
        """Write WAV bytes into the FIFO in a background thread (non-blocking)."""
        if not self._fifo_path:
            return

        def _write():
            try:
                with open(self._fifo_path, "wb") as f:
                    f.write(wav_bytes)
            except Exception:
                pass

        threading.Thread(target=_write, daemon=True).start()

    def stop(self):
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
            self._proc = None
        if self._fifo_path and os.path.exists(self._fifo_path):
            os.remove(self._fifo_path)
            self._fifo_path = None

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
