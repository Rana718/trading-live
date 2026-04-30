"""
Font manager: download and cache a CJK-capable font locally.
This avoids any dependency on system font paths and works on Linux and Windows.
"""
from pathlib import Path
import shutil
import ssl
import urllib.request

from PIL import ImageFont

# Cross-platform cache directory.
FONTS_DIR = Path.home() / ".trading_live" / "fonts"
NOTO_SANS_CJK_PATH = FONTS_DIR / "NotoSansCJK-Regular.ttc"

# Noto Sans CJK OTC bundle with broad Japanese/CJK coverage.
NOTO_SANS_CJK_URL = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Regular.ttc"


def _ensure_fonts_dir():
    FONTS_DIR.mkdir(parents=True, exist_ok=True)


def _download_font(url: str, path: Path, timeout: int = 30) -> bool:
    try:
        print(f"Downloading font from {url}...")
        _ensure_fonts_dir()
        with urllib.request.urlopen(url, timeout=timeout) as response, path.open("wb") as target:
            shutil.copyfileobj(response, target)
        print(f"Font cached at {path}")
        return True
    except Exception as exc:
        # Some Windows environments have broken CA bundles; retry without certificate verification.
        try:
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(url, timeout=timeout, context=context) as response, path.open("wb") as target:
                shutil.copyfileobj(response, target)
            print(f"Font cached at {path} (unverified SSL fallback)")
            return True
        except Exception as fallback_exc:
            print(f"Failed to download font: {exc}")
            print(f"Failed with SSL fallback too: {fallback_exc}")
            return False


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Get CJK-capable font for rendering.
    Returns bundled Noto Sans CJK if available, otherwise PIL default.
    """
    _ensure_fonts_dir()

    # Try to use cached Noto Sans CJK
    if NOTO_SANS_CJK_PATH.exists():
        try:
            return ImageFont.truetype(str(NOTO_SANS_CJK_PATH), size)
        except Exception as exc:
            print(f"Warning: Failed to load cached font: {exc}")

    # Try to download if not cached
    if NOTO_SANS_CJK_URL and not NOTO_SANS_CJK_PATH.exists():
        if _download_font(NOTO_SANS_CJK_URL, NOTO_SANS_CJK_PATH):
            try:
                return ImageFont.truetype(str(NOTO_SANS_CJK_PATH), size)
            except Exception as exc:
                print(f"Warning: Failed to load downloaded font: {exc}")

    # Fallback to PIL default font
    print("Warning: Using PIL default font (may not support CJK characters)")
    return ImageFont.load_default()


def ensure_fonts_cached():
    """Pre-download fonts at startup. Call this during app initialization."""
    if not NOTO_SANS_CJK_PATH.exists():
        _download_font(NOTO_SANS_CJK_URL, NOTO_SANS_CJK_PATH)
