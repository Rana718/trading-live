import subprocess
import threading
import tempfile
import os
import queue
import numpy as np
from PIL import Image
from config import WIDTH, HEIGHT, FPS, YOUTUBE_RTMP_URL, YOUTUBE_STREAM_KEY


class FFmpegStreamer:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._fifo_path: str | None = None
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._audio_writer_stop = threading.Event()
        self._audio_writer_thread: threading.Thread | None = None

    def start(self):
        # Create a named FIFO for audio
        self._fifo_path = tempfile.mktemp(suffix=".pcm.fifo")
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
                "-f", "s16le", "-ar", "44100", "-ac", "1", "-i", self._fifo_path,
                # encode
                "-vcodec", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
                "-b:v", "2500k", "-maxrate", "2500k", "-bufsize", "5000k",
                "-acodec", "aac", "-ar", "44100", "-b:a", "96k",
                "-f", "flv", rtmp_target,
            ],
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        self._audio_writer_stop.clear()
        self._audio_writer_thread = threading.Thread(target=self._audio_writer_loop, daemon=True)
        self._audio_writer_thread.start()

    def _wav_to_pcm(self, wav_bytes: bytes) -> bytes:
        with subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-i",
                "pipe:0",
                "-ac",
                "1",
                "-ar",
                "44100",
                "-f",
                "s16le",
                "pipe:1",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ) as proc:
            stdout, _ = proc.communicate(wav_bytes, timeout=30)
            return stdout or b""

    def _audio_writer_loop(self):
        silence = (b"\x00\x00" * 4410)  # 0.1s of mono 44.1kHz silence
        while not self._audio_writer_stop.is_set():
            if not self._fifo_path:
                break
            try:
                with open(self._fifo_path, "wb", buffering=0) as fifo:
                    while not self._audio_writer_stop.is_set() and self._fifo_path:
                        try:
                            pcm = self._audio_queue.get(timeout=0.1)
                        except queue.Empty:
                            fifo.write(silence)
                            continue

                        if pcm:
                            fifo.write(pcm)
                        else:
                            fifo.write(silence)
            except Exception:
                if not self._audio_writer_stop.is_set():
                    continue

    def send_frame(self, img: Image.Image):
        if self._proc and self._proc.stdin:
            try:
                self._proc.stdin.write(np.array(img.resize((WIDTH, HEIGHT))).tobytes())
            except BrokenPipeError:
                pass

    def play_audio(self, wav_bytes: bytes):
        """Queue WAV bytes for the persistent PCM writer."""
        if not self._fifo_path or not wav_bytes:
            return

        try:
            pcm = self._wav_to_pcm(wav_bytes)
            self._audio_queue.put_nowait(pcm)
        except Exception:
            return

    def stop(self):
        self._audio_writer_stop.set()
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
        self._audio_writer_thread = None

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
