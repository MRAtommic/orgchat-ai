"""
tts_engine.py - High-Quality Neural Text-to-Speech Engine for OrgChat AI
Powered by Microsoft Edge-TTS with in-memory caching and Thai text normalization.
"""

import os
import re
import io
import hashlib
import asyncio
from typing import Optional, Dict, Any

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# Available High Quality Neural Voices
AVAILABLE_VOICES = [
    {
        "id": "th-TH-PremwadeeNeural",
        "name": "เปรมวดี (เสียงหญิง - หวาน นุ่มนวล ชัดเจน)",
        "gender": "Female",
        "lang": "th-TH",
        "is_default": True
    },
    {
        "id": "th-TH-NiwatNeural",
        "name": "นิวัตน์ (เสียงชาย - สุภาพ ชัดเจน)",
        "gender": "Male",
        "lang": "th-TH",
        "is_default": False
    },
    {
        "id": "en-US-JennyNeural",
        "name": "Jenny (English - Natural Female)",
        "gender": "Female",
        "lang": "en-US",
        "is_default": False
    },
    {
        "id": "en-US-GuyNeural",
        "name": "Guy (English - Natural Male)",
        "gender": "Male",
        "lang": "en-US",
        "is_default": False
    }
]

DEFAULT_VOICE = "th-TH-PremwadeeNeural"

# In-Memory Cache (LRU up to 256 generated audio clips)
_AUDIO_CACHE: Dict[str, bytes] = {}
_CACHE_ORDER = []
_MAX_CACHE_SIZE = 256


def clean_text_for_tts(text: str) -> str:
    """
    Cleans markdown formatting, code blocks, URLs, HTML tags, and non-spoken symbols.
    """
    if not text:
        return ""

    # Remove code blocks ```...```
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code `...`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove markdown headers (#, ##, ###)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove raw URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove bold, italics, strikethrough (*, _, ~)
    text = re.sub(r'[\*_~]', '', text)
    # Remove emojis and special non-text characters
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    # Replace multiple newlines or spaces with single space
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def _get_cache_key(text: str, voice: str, rate: str, pitch: str) -> str:
    raw = f"{voice}:{rate}:{pitch}:{text}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


async def synthesize_speech_async(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> Optional[bytes]:
    """
    Asynchronously synthesizes speech using Edge-TTS and returns MP3 audio bytes.
    """
    if not EDGE_TTS_AVAILABLE:
        return None

    cleaned = clean_text_for_tts(text)
    if not cleaned:
        return None

    # Cap text length to 1,500 characters for snappy latency
    cleaned = cleaned[:1500]

    cache_key = _get_cache_key(cleaned, voice, rate, pitch)
    if cache_key in _AUDIO_CACHE:
        return _AUDIO_CACHE[cache_key]

    try:
        communicate = edge_tts.Communicate(
            text=cleaned,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        audio_buffer = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.extend(chunk["data"])

        audio_bytes = bytes(audio_buffer)

        # Cache management
        if len(_CACHE_ORDER) >= _MAX_CACHE_SIZE:
            oldest = _CACHE_ORDER.pop(0)
            _AUDIO_CACHE.pop(oldest, None)
        _AUDIO_CACHE[cache_key] = audio_bytes
        _CACHE_ORDER.append(cache_key)

        return audio_bytes
    except Exception as e:
        print(f"[TTSEngine Error] Failed to synthesize speech: {e}")
        return None


def synthesize_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> Optional[bytes]:
    """
    Synchronous wrapper for synthesize_speech_async.
    """
    try:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        asyncio.run,
                        synthesize_speech_async(text, voice, rate, pitch)
                    )
                    return future.result(timeout=15)
            else:
                return loop.run_until_complete(synthesize_speech_async(text, voice, rate, pitch))
        except RuntimeError:
            return asyncio.run(synthesize_speech_async(text, voice, rate, pitch))
    except Exception as e:
        print(f"[TTSEngine Sync Error]: {e}")
        return None
