"""Optional local speech-to-text support for the browser editor."""

from __future__ import annotations

import importlib.util
import os
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile


MAX_AUDIO_BYTES = 10 * 1024 * 1024
LANGUAGES = {"sa-IN": "sa", "hi-IN": "hi", "en-IN": "en"}
SUFFIXES = {
    "audio/webm": ".webm",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/ogg": ".ogg",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/aac": ".aac",
}


class SpeechError(ValueError):
    pass


class SpeechUnavailable(SpeechError):
    pass


def available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def model_name() -> str:
    return os.environ.get("SANSKRIT_STT_MODEL", "base")


@lru_cache(maxsize=1)
def _model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as error:
        raise SpeechUnavailable("Local transcription requires faster-whisper. Install requirements/speech.txt.") from error
    return WhisperModel(model_name(), device="cpu", compute_type="int8")


def transcribe_audio(data: bytes, language: str, content_type: str) -> str:
    """Transcribe a short browser recording without storing it after the request."""
    if language not in LANGUAGES:
        raise SpeechError("Choose Sanskrit, Hindi, or English for transcription")
    if not data:
        raise SpeechError("The audio recording is empty")
    if len(data) > MAX_AUDIO_BYTES:
        raise SpeechError("Audio is too large; record a shorter clip")
    mime = content_type.split(";", 1)[0].lower().strip()
    if mime not in SUFFIXES:
        raise SpeechError("Unsupported audio format")

    temporary = NamedTemporaryFile(suffix=SUFFIXES[mime], delete=False)
    path = Path(temporary.name)
    try:
        with temporary:
            temporary.write(data)
        try:
            segments, _ = _model().transcribe(
                str(path), language=LANGUAGES[language], beam_size=5,
                condition_on_previous_text=False,
            )
            return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()
        except SpeechUnavailable:
            raise
        except (OSError, RuntimeError, ValueError) as error:
            raise SpeechError(f"Transcription failed: {error}") from error
    finally:
        path.unlink(missing_ok=True)
