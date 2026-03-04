# sarvam_utils.py
"""
Sarvam AI – Pure REST API wrappers (no sarvamai SDK required).
Uses only `requests` which is available in the Flet web build.

Endpoints used:
  STT  : POST https://api.sarvam.ai/speech-to-text        (saaras:v3)
  TL   : POST https://api.sarvam.ai/translate              (mayura:v1)

Authentication: header  api-subscription-key: sk_aqm3d74w_15Z1tgVdVhrLR6CVjS8tpIiq

How to get your key:
  1. Go to https://dashboard.sarvam.ai
  2. Sign up / log in
  3. Copy your API Subscription Key
  4. Paste it below (replace the placeholder string)
"""

import os
import json

# ── Put your real key here ──────────────────────────────────────────────────
# Option A: hardcode for local dev/demo
SARVAM_KEY = os.environ.get("sk_rc853rl4_5uIuUN2Brd sme_retail_loan  kpKFqZia1T10vV", "YOUR_SARVAM_API_KEY_HERE")

# Option B (recommended for production): set environment variable before running
#   export SARVAM_API_KEY="your-real-key"
#   flet run main.py
# ────────────────────────────────────────────────────────────────────────────

STT_URL       = "https://api.sarvam.ai/speech-to-text"
TRANSLATE_URL = "https://api.sarvam.ai/translate"


def _headers_json() -> dict:
    return {
        "api-subscription-key": SARVAM_KEY,
        "Content-Type": "application/json",
    }


def is_key_configured() -> bool:
    """Returns True if a real key has been set (not the placeholder)."""
    return bool(SARVAM_KEY) and SARVAM_KEY != "YOUR_SARVAM_API_KEY_HERE"


# ── Speech-to-Text ──────────────────────────────────────────────────────────

def stt_from_bytes(audio_bytes: bytes, filename: str = "audio.wav",
                   lang: str = "en-IN") -> str:
    """
    Transcribe raw audio bytes using Sarvam Saaras v3.

    Parameters
    ----------
    audio_bytes : bytes   Raw audio content (WAV / WebM / MP3 etc.)
    filename    : str     Filename hint – extension tells the API the format
    lang        : str     BCP-47 language code, e.g. 'en-IN', 'hi-IN', 'kn-IN'

    Returns
    -------
    str   Transcribed text, or an error string prefixed with '[Error]'
    """
    if not is_key_configured():
        return "[Mock STT] Add your SARVAM_API_KEY to sarvam_utils.py"

    try:
        import requests
        files = {"file": (filename, audio_bytes, _mime(filename))}
        data  = {
            "model":         "saaras:v3",
            "mode":          "transcribe",
            "language_code": lang,
        }
        headers = {"api-subscription-key": SARVAM_KEY}
        resp = requests.post(STT_URL, headers=headers, files=files,
                             data=data, timeout=30)
        resp.raise_for_status()
        return resp.json().get("transcript", "")
    except Exception as e:
        return f"[STT Error] {e}"


def stt_from_file(wav_path: str, lang: str = "en-IN") -> str:
    """Convenience wrapper – reads a file from disk and calls stt_from_bytes."""
    if not is_key_configured():
        return "[Mock STT] Add your SARVAM_API_KEY to sarvam_utils.py"
    try:
        with open(wav_path, "rb") as f:
            audio_bytes = f.read()
        ext = wav_path.rsplit(".", 1)[-1].lower() if "." in wav_path else "wav"
        return stt_from_bytes(audio_bytes, filename=f"audio.{ext}", lang=lang)
    except Exception as e:
        return f"[STT File Error] {e}"


def _mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"
    return {
        "wav":  "audio/wav",
        "mp3":  "audio/mpeg",
        "ogg":  "audio/ogg",
        "webm": "audio/webm",
        "m4a":  "audio/mp4",
        "flac": "audio/flac",
    }.get(ext, "audio/wav")


# ── Text Translation ─────────────────────────────────────────────────────────

def translate_text(text: str,
                   source_lang: str = "en-IN",
                   target_lang: str = "hi-IN") -> str:
    """
    Translate text using Sarvam Mayura v1.

    Parameters
    ----------
    text        : str   Input text (max ~1000 chars per call)
    source_lang : str   BCP-47 source language code
    target_lang : str   BCP-47 target language code

    Returns
    -------
    str   Translated text, or original text on failure
    """
    if not is_key_configured():
        return f"[Mock Translation] {text}"

    try:
        import requests
        payload = {
            "input":                text[:1000],
            "source_language_code": source_lang,
            "target_language_code": target_lang,
            "model":                "mayura:v1",
            "enable_preprocessing": True,
        }
        resp = requests.post(TRANSLATE_URL, headers=_headers_json(),
                             json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json().get("translated_text", text)
    except Exception as e:
        return f"[Translation Error] {e}"


def translate_to_hindi(text: str) -> str:
    """Shorthand: English → Hindi."""
    return translate_text(text, source_lang="en-IN", target_lang="hi-IN")


def translate_to_kannada(text: str) -> str:
    """Shorthand: English → Kannada (great for Bengaluru demos)."""
    return translate_text(text, source_lang="en-IN", target_lang="kn-IN")


# ── Quick CLI test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Sarvam key configured:", is_key_configured())
    result = translate_to_hindi("Loan approved. FOIR is within acceptable limits.")
    print("Hindi:", result)
