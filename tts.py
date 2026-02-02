import io
import threading
import asyncio
import re
import edge_tts
import sounddevice as sd
import soundfile as sf

VOICE = "it-IT-ElsaNeural"

stop_speaking_flag = threading.Event()


def normalize_punctuation(text: str) -> str:
    """Optimize text for better TTS flow."""
    text = re.sub(r'\.\s+', ', ', text)  # period
    text = re.sub(r'!\s+', ', ', text)   # exclamation point
    text = re.sub(r'\?\s+', ', ', text)  # question mark

    if text.endswith("."):
        text = text[:-1]

    return text.strip()


def edge_speak(text: str, ui=None, blocking=True):
    if not text.strip():
        return

    finished_event = threading.Event()

    def _thread():
        if ui:
            ui.start_speaking()
        stop_speaking_flag.clear()

        try:
            # Run async edge_tts in sync context
            asyncio.run(_async_speak(text, ui))
        except Exception as e:
            print("VOICE ERROR:", e)
        finally:
            if ui:
                ui.stop_speaking()
            finished_event.set()

    threading.Thread(target=_thread, daemon=True).start()

    if blocking:
        finished_event.wait()


async def _async_speak(text: str, ui=None):
    """Internal async function to handle edge-tts with optimized buffering."""
    optimized_text = normalize_punctuation(text)

    communicate = edge_tts.Communicate(
        optimized_text,
        VOICE,
        pitch="+2Hz",
        rate="+8%"
    )

    # Accumula tutto l'audio - più stabile, evita errori di decodifica
    audio_buffer = bytearray()

    async for chunk in communicate.stream():
        if stop_speaking_flag.is_set():
            break
        if chunk["type"] == "audio":
            audio_buffer.extend(chunk["data"])

    if stop_speaking_flag.is_set() or len(audio_buffer) == 0:
        return

    # Decodifica una volta sola quando abbiamo tutto l'audio
    wav_bytes = io.BytesIO(bytes(audio_buffer))

    try:
        data, samplerate = sf.read(wav_bytes, dtype="float32")
    except Exception as e:
        print(f"Audio decode error: {e}")
        return

    # Riproduci tutto l'audio
    channels = data.shape[1] if len(data.shape) > 1 else 1
    with sd.OutputStream(
        samplerate=samplerate,
        channels=channels,
        dtype="float32"
    ) as stream:
        block_size = 2048
        for start in range(0, len(data), block_size):
            if stop_speaking_flag.is_set():
                break
            stream.write(data[start:start + block_size])


def stop_speaking():
    stop_speaking_flag.set()
