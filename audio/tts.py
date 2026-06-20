import asyncio
import importlib
import os
import subprocess
import tempfile
import time

from edge_tts import Communicate


def _cfg():
    import config
    importlib.reload(config)
    return config


def _edge_tts_to_wav(text: str) -> bytes:
    cfg = _cfg()

    async def _synthesize() -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3_path = f.name
        try:
            await Communicate(
                text=text,
                voice=cfg.EDGE_TTS_VOICE,
                rate=cfg.EDGE_TTS_RATE,
                volume=cfg.EDGE_TTS_VOLUME,
            ).save(mp3_path)
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", "44100", "-f", "wav", "pipe:1"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
            )
            return result.stdout
        finally:
            try:
                os.remove(mp3_path)
            except OSError:
                pass

    return asyncio.run(_synthesize())


def synthesize(text: str, retries: int = 3, backoff: float = 0.5) -> bytes:
    """Generate WAV audio bytes using Edge TTS, reading voice config fresh each call."""
    if _cfg().TTS_ENGINE != "edge":
        return b""
    for attempt in range(1, retries + 1):
        try:
            return _edge_tts_to_wav(text)
        except Exception:
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                return b""
