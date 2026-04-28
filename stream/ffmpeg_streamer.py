import subprocess
import threading
import tempfile
import os
import queue
import time
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
        self._ffmpeg_log_thread: threading.Thread | None = None

    def start(self):
        # Create a named FIFO for audio
        self._fifo_path = tempfile.mktemp(suffix=".pcm.fifo")
        os.mkfifo(self._fifo_path)

        # Start audio writer thread before FFmpeg so FIFO is ready
        self._audio_writer_stop.clear()
        self._audio_writer_thread = threading.Thread(target=self._audio_writer_loop, daemon=True)
        self._audio_writer_thread.start()

        # Give the writer thread a moment to open the FIFO
        time.sleep(0.1)

        rtmp_target = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"

        # Main FFmpeg: video from stdin, audio from FIFO
        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y", "-loglevel", "info",
                # video
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
                "-r", str(FPS), "-i", "pipe:0",
                # audio from fifo (always has silence or narration)
                "-f", "s16le", "-ar", "44100", "-ac", "1", "-i", self._fifo_path,
                # encode
                "-vcodec", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
                "-b:v", "2500k", "-minrate", "2500k", "-maxrate", "2500k", "-bufsize", "5000k",
                "-x264-params", f"nal-hrd=cbr:force-cfr=1:keyint={FPS * 2}:min-keyint={FPS * 2}:scenecut=0",
                "-acodec", "aac", "-ar", "44100", "-b:a", "128k",
                "-f", "flv", rtmp_target,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )

        # Start a thread to tail FFmpeg logs so output buffer doesn't block
        self._ffmpeg_log_thread = threading.Thread(target=self._read_ffmpeg_logs, daemon=True)
        self._ffmpeg_log_thread.start()

    def _read_ffmpeg_logs(self):
        """Read FFmpeg stdout/stderr to prevent buffer blocking."""
        if not self._proc or not self._proc.stdout:
            return
        try:
            for line in iter(self._proc.stdout.readline, b""):
                if not line:
                    break
                msg = line.decode("utf-8", errors="ignore").strip()
                if msg and ("error" in msg.lower() or "bitrate" in msg.lower() or "fps=" in msg):
                    print(f"[FFmpeg] {msg}")
        except Exception:
            pass

    def _wav_to_pcm(self, wav_bytes: bytes) -> bytes:
        try:
            with subprocess.Popen(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", "pipe:0",
                    "-ac", "1",
                    "-ar", "44100",
                    "-f", "s16le",
                    "pipe:1",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as proc:
                stdout, stderr = proc.communicate(wav_bytes, timeout=30)
                if proc.returncode != 0:
                    print(f"[WAV->PCM ERROR] {stderr.decode()[:200]}")
                    return b""
                return stdout or b""
        except Exception as e:
            print(f"[WAV->PCM Exception] {e}")
            return b""

    def _audio_writer_loop(self):
        silence = (b"\x00\x00" * 4410)  # 0.1s of mono 44.1kHz silence
        
        # Pre-fill queue with 2 seconds of silence so audio is ready immediately
        for _ in range(20):
            self._audio_queue.put_nowait(silence)
        
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
                self._proc.stdin.flush()
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
