import subprocess
import threading
import tempfile
import os
import platform
import queue
import time
import numpy as np
from PIL import Image
from config import WIDTH, HEIGHT, FPS, YOUTUBE_RTMP_URL, YOUTUBE_STREAM_KEY

MUSIC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "music.mp3")
MUSIC_VOLUME = 0.50  # background music volume
_CHUNK = 4410 * 2    # bytes: 0.1s of mono s16le @ 44100Hz (4410 samples × 2 bytes)


def _mix_pcm(music_chunk: bytes, voice_chunk: bytes) -> bytes:
    """Mix music (low volume) + voice (full volume), clamp to s16 range."""
    music = np.frombuffer(music_chunk, dtype=np.int16).astype(np.float32) * MUSIC_VOLUME
    voice = np.frombuffer(voice_chunk, dtype=np.int16).astype(np.float32)
    return np.clip(music + voice, -32768, 32767).astype(np.int16).tobytes()


class _MusicReader:
    """Streams looping music PCM into an internal queue from a background thread."""

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._buf = bytearray()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self):
        if not os.path.exists(MUSIC_PATH):
            print(f"[Music] File not found: {MUSIC_PATH}")
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._thread.start()
        print("[Music] Background music stream started.")

    def _reader_loop(self):
        while not self._stop.is_set():
            try:
                proc = subprocess.Popen(
                    ["ffmpeg", "-loglevel", "error",
                     "-stream_loop", "-1", "-i", MUSIC_PATH,
                     "-ac", "1", "-ar", "44100", "-f", "s16le", "pipe:1"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                )
                self._proc = proc
                while not self._stop.is_set():
                    chunk = proc.stdout.read(8192)
                    if not chunk:
                        break
                    with self._lock:
                        self._buf += chunk
                        # Keep buffer bounded to ~2s (176400 bytes) to avoid unbounded growth
                        if len(self._buf) > 176400:
                            del self._buf[:len(self._buf) - 176400]
                proc.kill()
            except Exception as e:
                print(f"[Music] reader error: {e}")
                time.sleep(1)

    def read(self, size: int) -> bytes:
        """Return `size` bytes of music PCM; returns silence if buffer not yet filled."""
        with self._lock:
            if len(self._buf) >= size:
                out = bytes(self._buf[:size])
                del self._buf[:size]
                return out
        # Not enough buffered yet — return silence (music will catch up)
        return b"\x00" * size

    def stop(self):
        self._stop.set()
        if self._proc:
            self._proc.kill()
            self._proc = None


class FFmpegStreamer:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._fifo_path: str | None = None
        self._use_fifo = hasattr(os, "mkfifo") and platform.system().lower() != "windows"
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._audio_writer_stop = threading.Event()
        self._audio_writer_thread: threading.Thread | None = None
        self._ffmpeg_log_thread: threading.Thread | None = None
        self._music = _MusicReader()

    def start(self):
        # Start looping music stream
        self._music.start()

        audio_input_args: list[str]

        if self._use_fifo:
            # Create a named FIFO for audio on POSIX systems.
            self._fifo_path = tempfile.mktemp(suffix=".pcm.fifo")
            os.mkfifo(self._fifo_path)

            # Start audio writer thread before FFmpeg so FIFO is ready.
            self._audio_writer_stop.clear()
            self._audio_writer_thread = threading.Thread(target=self._audio_writer_loop, daemon=True)
            self._audio_writer_thread.start()

            # Give the writer thread a moment to open the FIFO.
            time.sleep(0.1)
            audio_input_args = ["-f", "s16le", "-ar", "44100", "-ac", "1", "-i", self._fifo_path]
        else:
            # Windows fallback: keep a continuous silent audio source so the stream starts cleanly.
            # Narration audio requires a separate Windows-specific pipe implementation.
            self._fifo_path = None
            self._audio_writer_stop.clear()
            self._audio_writer_thread = None
            audio_input_args = [
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
            ]

        rtmp_target = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"

        # Main FFmpeg: video from stdin, audio from FIFO or silent fallback
        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y", "-loglevel", "info",
                # video
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
                "-r", str(FPS), "-i", "pipe:0",
                # audio from fifo (always has silence or narration) or silent fallback on Windows
                *audio_input_args,
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
        silence = b"\x00\x00" * 4410  # 0.1s of s16le mono silence

        # Pre-fill queue with 2 seconds of silence
        for _ in range(20):
            self._audio_queue.put_nowait(silence)

        while not self._audio_writer_stop.is_set():
            if not self._fifo_path:
                break
            try:
                with open(self._fifo_path, "wb", buffering=0) as fifo:
                    while not self._audio_writer_stop.is_set() and self._fifo_path:
                        try:
                            voice_pcm = self._audio_queue.get(timeout=0.1)
                        except queue.Empty:
                            voice_pcm = silence

                        # Write voice PCM mixed with music in _CHUNK-sized pieces
                        for offset in range(0, max(len(voice_pcm), _CHUNK), _CHUNK):
                            v_chunk = voice_pcm[offset:offset + _CHUNK]
                            # Pad short final chunk with silence
                            if len(v_chunk) < _CHUNK:
                                v_chunk = v_chunk + b"\x00" * (_CHUNK - len(v_chunk))
                            music_chunk = self._music.read(_CHUNK)
                            fifo.write(_mix_pcm(music_chunk, v_chunk))
            except Exception:
                if not self._audio_writer_stop.is_set():
                    continue

    def send_frame(self, img: Image.Image):
        if self._proc and self._proc.stdin:
            try:
                self._proc.stdin.write(np.array(img).tobytes())
                self._proc.stdin.flush()
            except BrokenPipeError:
                pass

    def play_audio(self, wav_bytes: bytes):
        """Queue WAV bytes for the persistent PCM writer."""
        if not self._use_fifo or not self._fifo_path or not wav_bytes:
            return

        try:
            pcm = self._wav_to_pcm(wav_bytes)
            self._audio_queue.put_nowait(pcm)
        except Exception:
            return

    def stop(self):
        self._audio_writer_stop.set()
        self._music.stop()
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
