import requests
import io
from config import VOICEVOX_URL, VOICEVOX_SPEAKER


def synthesize(text: str) -> bytes:
    """Call VOICEVOX and return WAV audio bytes."""
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
