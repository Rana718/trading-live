import subprocess
import threading
import tempfile
import os
import platform
import queue
import time
import numpy as np
from PIL import Image
from config import WIDTH, HEIGHT, FPS, YOUTUBE_RTMP_URL, YOUTUBE_STREAM_KEY, VIDEO_BITRATE

MUSIC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "music.mp3")
MUSIC_VOLUME = 0.45
_SAMPLE_RATE = 44100
_CHUNK = _SAMPLE_RATE // 10 * 2  # 0.1s of mono s16le


def _mix_pcm(music_chunk: bytes, voice_chunk: bytes) -> bytes:
    music = np.frombuffer(music_chunk, dtype=np.int16).astype(np.float32) * MUSIC_VOLUME
    voice = np.frombuffer(voice_chunk, dtype=np.int16).astype(np.float32)
    return np.clip(music + voice, -32768, 32767).astype(np.int16).tobytes()


class _MusicReader:
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

    def _reader_loop(self):
        while not self._stop.is_set():
            try:
                proc = subprocess.Popen(
                    ["ffmpeg", "-loglevel", "error",
                     "-stream_loop", "-1", "-i", MUSIC_PATH,
                     "-ac", "1", "-ar", str(_SAMPLE_RATE), "-f", "s16le", "pipe:1"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                )
                self._proc = proc
                while not self._stop.is_set():
                    chunk = proc.stdout.read(8192)
                    if not chunk:
                        break
                    with self._lock:
                        self._buf += chunk
                        if len(self._buf) > _SAMPLE_RATE * 2 * 2:  # cap at 2s
                            del self._buf[:len(self._buf) - _SAMPLE_RATE * 2 * 2]
                proc.kill()
            except Exception as e:
                print(f"[Music] error: {e}")
                time.sleep(1)

    def read(self, size: int) -> bytes:
        with self._lock:
            if len(self._buf) >= size:
                out = bytes(self._buf[:size])
                del self._buf[:size]
                return out
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
        self._audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=10)
        self._audio_writer_stop = threading.Event()
        self._audio_writer_thread: threading.Thread | None = None
        self._ffmpeg_log_thread: threading.Thread | None = None
        self._music = _MusicReader()

    def start(self):
        self._music.start()

        if self._use_fifo:
            self._fifo_path = tempfile.mktemp(suffix=".pcm.fifo")
            os.mkfifo(self._fifo_path)
            self._audio_writer_stop.clear()
            self._audio_writer_thread = threading.Thread(target=self._audio_writer_loop, daemon=True)
            self._audio_writer_thread.start()
            time.sleep(0.1)
            audio_input_args = ["-f", "s16le", "-ar", str(_SAMPLE_RATE), "-ac", "1", "-i", self._fifo_path]
        else:
            self._fifo_path = None
            audio_input_args = ["-f", "lavfi", "-i", f"anullsrc=channel_layout=mono:sample_rate={_SAMPLE_RATE}"]

        # Choose x264 preset based on bitrate (lower quality = faster preset for low-end CPUs)
        bitrate_k = int(VIDEO_BITRATE.replace("k", ""))
        x264_preset = "veryfast" if bitrate_k >= 2000 else "superfast" if bitrate_k >= 800 else "ultrafast"
        audio_bitrate = "128k" if bitrate_k >= 2000 else "96k" if bitrate_k >= 800 else "64k"

        rtmp_target = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"
        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y", "-loglevel", "warning",
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
                "-r", str(FPS), "-i", "pipe:0",
                *audio_input_args,
                "-vcodec", "libx264", "-preset", x264_preset, "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
                "-b:v", VIDEO_BITRATE, "-maxrate", VIDEO_BITRATE,
                "-bufsize", str(bitrate_k * 2) + "k",
                "-acodec", "aac", "-ar", str(_SAMPLE_RATE), "-b:a", audio_bitrate,
                "-f", "flv", rtmp_target,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self._ffmpeg_log_thread = threading.Thread(target=self._read_ffmpeg_logs, daemon=True)
        self._ffmpeg_log_thread.start()

    def _read_ffmpeg_logs(self):
        if not self._proc or not self._proc.stdout:
            return
        try:
            for line in iter(self._proc.stdout.readline, b""):
                msg = line.decode("utf-8", errors="ignore").strip()
                if msg:
                    print(f"[FFmpeg] {msg}")
        except Exception:
            pass

    def _wav_to_pcm(self, wav_bytes: bytes) -> bytes:
        try:
            with subprocess.Popen(
                ["ffmpeg", "-y", "-loglevel", "error",
                 "-i", "pipe:0", "-ac", "1", "-ar", str(_SAMPLE_RATE), "-f", "s16le", "pipe:1"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ) as proc:
                stdout, stderr = proc.communicate(wav_bytes, timeout=30)
                if proc.returncode != 0:
                    print(f"[WAV->PCM] {stderr.decode()[:200]}")
                    return b""
                return stdout or b""
        except Exception as e:
            print(f"[WAV->PCM] {e}")
            return b""

    def _audio_writer_loop(self):
        silence = b"\x00" * _CHUNK

        # Pre-fill 2s of silence
        for _ in range(20):
            self._audio_queue.put_nowait(silence)

        while not self._audio_writer_stop.is_set():
            if not self._fifo_path:
                break
            try:
                # Open FIFO in non-blocking mode so re-open after error doesn't deadlock
                fd = os.open(self._fifo_path, os.O_WRONLY | os.O_NONBLOCK)
                with os.fdopen(fd, "wb", buffering=0) as fifo:
                    while not self._audio_writer_stop.is_set() and self._fifo_path:
                        try:
                            voice_pcm = self._audio_queue.get(timeout=0.05)
                        except queue.Empty:
                            voice_pcm = silence

                        for offset in range(0, max(len(voice_pcm), _CHUNK), _CHUNK):
                            v_chunk = voice_pcm[offset:offset + _CHUNK]
                            if len(v_chunk) < _CHUNK:
                                v_chunk = v_chunk + b"\x00" * (_CHUNK - len(v_chunk))
                            music_chunk = self._music.read(_CHUNK)
                            try:
                                fifo.write(_mix_pcm(music_chunk, v_chunk))
                            except OSError:
                                break
            except OSError:
                # FIFO read end not ready yet or broken — wait and retry
                time.sleep(0.1)
            except Exception as e:
                if not self._audio_writer_stop.is_set():
                    print(f"[Audio writer] {e}")
                    time.sleep(0.1)

    def send_frame(self, img: Image.Image):
        if self._proc and self._proc.stdin:
            try:
                self._proc.stdin.write(np.array(img).tobytes())
                self._proc.stdin.flush()
            except BrokenPipeError:
                pass

    def play_audio(self, wav_bytes: bytes):
        if not self._use_fifo or not self._fifo_path or not wav_bytes:
            return
        pcm = self._wav_to_pcm(wav_bytes)
        if not pcm:
            return
        try:
            # Drop oldest if queue is full (prevents memory build-up on slow machines)
            if self._audio_queue.full():
                try:
                    self._audio_queue.get_nowait()
                except queue.Empty:
                    pass
            self._audio_queue.put_nowait(pcm)
        except Exception:
            pass

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
