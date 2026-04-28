import requests
import time
import io
from requests.exceptions import RequestException
from config import VOICEVOX_URL, VOICEVOX_SPEAKER


def synthesize(text: str, retries: int = 3, backoff: float = 0.5) -> bytes:
    """Call VOICEVOX and return WAV audio bytes.

    If VOICEVOX is unreachable, retry a few times then return empty bytes as a safe fallback.
    """
    for attempt in range(1, retries + 1):
        try:
            # Step 1: create audio query
            query_resp = requests.post(
                f"{VOICEVOX_URL}/audio_query",
                params={"text": text, "speaker": VOICEVOX_SPEAKER},
                timeout=15,
            )
            query_resp.raise_for_status()

            # Step 2: synthesize
            synth_resp = requests.post(
                f"{VOICEVOX_URL}/synthesis",
                params={"speaker": VOICEVOX_SPEAKER},
                json=query_resp.json(),
                timeout=30,
            )
            synth_resp.raise_for_status()
            return synth_resp.content  # WAV bytes

        except RequestException:
            if attempt < retries:
                time.sleep(backoff * attempt)
                continue
            # Final fallback: return empty bytes so caller can proceed without audio
            return b""
