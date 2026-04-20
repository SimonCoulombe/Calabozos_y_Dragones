#!/usr/bin/env python3
"""Wyoming-protocol Piper TTS client.

Saves audio as WAV (Anki supports WAV natively; no ffmpeg required).

Usage:
    ok = synthesize_to_wav("espada", Path("/tmp/espada.wav"), host="192.168.2.15", port=10201)
"""

import asyncio
import io
import logging
import wave
from pathlib import Path

log = logging.getLogger(__name__)


async def _synthesize_async(text: str, host: str, port: int) -> bytes:
    """Connect to a Wyoming Piper server and return proper WAV bytes."""
    from wyoming.audio import AudioChunk, AudioStart, AudioStop
    from wyoming.client import AsyncTcpClient
    from wyoming.tts import Synthesize

    audio_chunks: list[bytes] = []
    rate = 22050
    channels = 1
    sampwidth = 2  # 16-bit PCM

    async with AsyncTcpClient(host, port) as client:
        await client.write_event(Synthesize(text=text).event())
        while True:
            event = await client.read_event()
            if event is None:
                break
            if AudioStart.is_type(event.type):
                info = AudioStart.from_event(event)
                rate = info.rate
                channels = info.channels
                sampwidth = info.width
            elif AudioChunk.is_type(event.type):
                chunk = AudioChunk.from_event(event)
                audio_chunks.append(chunk.audio)
            elif AudioStop.is_type(event.type):
                break

    raw_pcm = b"".join(audio_chunks)
    if not raw_pcm:
        return b""

    # Prepend 200ms of silence so PipeWire/ALSA doesn't clip the first syllable
    silence_frames = int(0.20 * rate)
    padded_pcm = (b"\x00" * silence_frames * channels * sampwidth) + raw_pcm

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(padded_pcm)
    return wav_io.getvalue()


def synthesize_to_wav(
    text: str,
    out_path: Path,
    host: str,
    port: int,
    skip_on_failure: bool = True,
) -> bool:
    """Synthesize Spanish text to a WAV file via a Wyoming Piper server. Returns True on success."""
    # Strip characters that can confuse TTS servers (ellipsis, ¿, ¡, …)
    tts_text = text.replace("…", "").replace("¿", "").replace("¡", "").strip()
    if not tts_text:
        return False

    try:
        wav_bytes = asyncio.run(asyncio.wait_for(_synthesize_async(tts_text, host, port), timeout=20))
    except asyncio.TimeoutError:
        if skip_on_failure:
            log.warning("TTS timeout for %r", text)
            return False
        raise
    except Exception as e:
        if skip_on_failure:
            log.warning("TTS unavailable for %r: %s", text, e)
            return False
        raise

    if not wav_bytes:
        log.warning("TTS returned empty audio for %r", text)
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(wav_bytes)
    return True


if __name__ == "__main__":
    import sys
    import yaml

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    tts = config["tts"]

    text = sys.argv[1] if len(sys.argv) > 1 else "hola"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/test_es.wav")

    ok = synthesize_to_wav(text, out, tts["host"], tts["port"])
    print("OK →", out if ok else "FAILED (TTS server unreachable?)")
