import subprocess
import threading
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
_CHUNK = _SAMPLE_RATE // 10 * 2  # 0.1s mono s16le
_IS_WINDOWS = platform.system().lower() == "windows"


def _mix_pcm(music_chunk: bytes, voice_chunk: bytes) -> bytes:
    music = np.frombuffer(music_chunk, dtype=np.int16).astype(np.float32) * MUSIC_VOLUME
    voice = np.frombuffer(voice_chunk, dtype=np.int16).astype(np.float32)
    return np.clip(music + voice, -32768, 32767).astype(np.int16).tobytes()


class _MusicReader:
    """Decodes music.mp3 fully into memory once, then loops it seamlessly."""

    def __init__(self):
        self._pcm: bytes = b""
        self._pos: int = 0
        self._lock = threading.Lock()

    def start(self):
        if not os.path.exists(MUSIC_PATH):
            print(f"[Music] Not found: {MUSIC_PATH}")
            return
        try:
            print("[Music] Decoding music file into memory...")
            result = subprocess.run(
                ["ffmpeg", "-loglevel", "error",
                 "-i", MUSIC_PATH,
                 "-ac", "1", "-ar", str(_SAMPLE_RATE), "-f", "s16le", "pipe:1"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
            )
            if result.returncode != 0:
                print(f"[Music] Decode error: {result.stderr.decode()[:200]}")
                return
            self._pcm = result.stdout
            print(f"[Music] Loaded {len(self._pcm) // 1024}KB PCM, duration ~{len(self._pcm) / (_SAMPLE_RATE * 2):.1f}s")
        except Exception as e:
            print(f"[Music] Failed to load: {e}")

    def read(self, size: int) -> bytes:
        if not self._pcm:
            return b"\x00" * size
        with self._lock:
            end = self._pos + size
            if end <= len(self._pcm):
                out = self._pcm[self._pos:end]
                self._pos = end
            else:
                # Wrap around seamlessly
                out = self._pcm[self._pos:]
                remaining = size - len(out)
                self._pos = remaining % len(self._pcm)
                out = out + self._pcm[:self._pos]
            return out

    def stop(self):
        pass  # nothing to clean up


class FFmpegStreamer:
    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._voice_queue: queue.Queue[bytes] = queue.Queue(maxsize=10)
        self._mixer_stop = threading.Event()
        self._mixer_thread: threading.Thread | None = None
        self._log_thread: threading.Thread | None = None
        self._music = _MusicReader()
        self._audio_w: int | None = None

    def start(self):
        self._music.start()
        self._mixer_stop.clear()

        bitrate_k = int(VIDEO_BITRATE.replace("k", ""))
        x264_preset = "veryfast" if bitrate_k >= 2000 else "superfast" if bitrate_k >= 800 else "ultrafast"
        audio_bitrate = "128k" if bitrate_k >= 2000 else "96k" if bitrate_k >= 800 else "64k"
        rtmp_target = f"{YOUTUBE_RTMP_URL}/{YOUTUBE_STREAM_KEY}"

        audio_r, self._audio_w = os.pipe()

        popen_kwargs: dict = dict(
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        if _IS_WINDOWS:
            # Windows: close_fds=False lets child inherit all open fds
            popen_kwargs["close_fds"] = False
        else:
            # Linux/macOS: must explicitly whitelist fd via pass_fds
            popen_kwargs["pass_fds"] = (audio_r,)

        self._proc = subprocess.Popen(
            [
                "ffmpeg", "-y", "-loglevel", "warning",
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
                "-r", str(FPS), "-i", "pipe:0",
                "-f", "s16le", "-ar", str(_SAMPLE_RATE), "-ac", "1",
                "-i", f"pipe:{audio_r}",
                "-vcodec", "libx264", "-preset", x264_preset, "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-g", str(FPS * 2),
                "-b:v", VIDEO_BITRATE, "-maxrate", VIDEO_BITRATE,
                "-bufsize", str(bitrate_k * 2) + "k",
                "-acodec", "aac", "-ar", str(_SAMPLE_RATE), "-b:a", audio_bitrate,
                "-f", "flv", rtmp_target,
            ],
            **popen_kwargs,
        )

        # Close read end in parent — FFmpeg owns it now
        os.close(audio_r)

        self._mixer_thread = threading.Thread(target=self._mixer_loop, daemon=True)
        self._mixer_thread.start()

        self._log_thread = threading.Thread(target=self._read_logs, daemon=True)
        self._log_thread.start()

    def _mixer_loop(self):
        silence = b"\x00" * _CHUNK
        chunk_duration = (_CHUNK // 2) / _SAMPLE_RATE

        audio_wfile = os.fdopen(self._audio_w, "wb", buffering=0)
        self._audio_w = None
        next_tick = time.monotonic()
        try:
            while not self._mixer_stop.is_set():
                try:
                    voice_pcm = self._voice_queue.get_nowait()
                except queue.Empty:
                    voice_pcm = silence

                for offset in range(0, max(len(voice_pcm), _CHUNK), _CHUNK):
                    v = voice_pcm[offset:offset + _CHUNK]
                    if len(v) < _CHUNK:
                        v = v + b"\x00" * (_CHUNK - len(v))
                    m = self._music.read(_CHUNK)
                    try:
                        audio_wfile.write(_mix_pcm(m, v))
                    except (BrokenPipeError, OSError):
                        return
                    next_tick += chunk_duration
                    sleep = next_tick - time.monotonic()
                    if sleep > 0:
                        time.sleep(sleep)
        finally:
            try:
                audio_wfile.close()
            except Exception:
                pass

    def _read_logs(self):
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

    def send_frame(self, img: Image.Image):
        if self._proc and self._proc.stdin:
            try:
                self._proc.stdin.write(np.array(img).tobytes())
                self._proc.stdin.flush()
            except BrokenPipeError:
                pass

    def play_audio(self, wav_bytes: bytes):
        if not wav_bytes:
            return
        pcm = self._wav_to_pcm(wav_bytes)
        if not pcm:
            return
        if self._voice_queue.full():
            try:
                self._voice_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self._voice_queue.put_nowait(pcm)
        except queue.Full:
            pass

    def stop(self):
        self._mixer_stop.set()
        self._music.stop()
        if self._audio_w is not None:
            try:
                os.close(self._audio_w)
            except Exception:
                pass
            self._audio_w = None
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
