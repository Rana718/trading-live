import asyncio
import os
import subprocess
import tempfile
import time

from edge_tts import Communicate

from config import EDGE_TTS_RATE, EDGE_TTS_VOLUME, EDGE_TTS_VOICE, TTS_ENGINE


def _edge_tts_to_wav(text: str) -> bytes:
    async def _synthesize() -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as mp3_file:
            mp3_path = mp3_file.name

        try:
            await Communicate(
                text=text,
                voice=EDGE_TTS_VOICE,
                rate=EDGE_TTS_RATE,
                volume=EDGE_TTS_VOLUME,
            ).save(mp3_path)

            result = subprocess.run(
                ["ffmpeg", "-y", "-i", mp3_path, "-f", "wav", "pipe:1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return result.stdout
        finally:
            try:
                os.remove(mp3_path)
            except OSError:
                pass

    return asyncio.run(_synthesize())


def synthesize(text: str, retries: int = 3, backoff: float = 0.5) -> bytes:
    """Generate WAV audio bytes using Edge TTS.

    If Edge TTS is unreachable, retry a few times then return empty bytes as a safe fallback.
    """
    if TTS_ENGINE != "edge":
        return b""

    for attempt in range(1, retries + 1):
        try:
            return _edge_tts_to_wav(text)
        except Exception:
            if attempt < retries:
                time.sleep(backoff * attempt)
                continue
            return b""
