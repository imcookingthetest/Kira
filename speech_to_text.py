import sounddevice as sd
import vosk
import queue
import sys
import json
import threading

# Use small model for faster response (download from: https://alphacephei.com/vosk/models)
# Small model: vosk-model-small-it-0.22 (~40MB, 5-10x faster)
# Full model: vosk-model-it-0.22 (~1.5GB, more accurate but slower)
MODEL_PATH = r"C:\Users\loren\Downloads\vosk-model-it-0.22\vosk-model-it-0.22"  # Raw string per Windows path
# Alternative: usa forward slash che funziona anche su Windows
# MODEL_PATH = "C:/Users/loren/Downloads/vosk-model-it-0.22/vosk-model-it-0.22"
model = vosk.Model(MODEL_PATH)

q = queue.Queue()
stop_listening_flag = threading.Event()

def callback(indata, frames, time, status):
    if status:
        # Handle input overflow by clearing queue
        if "overflow" in str(status).lower():
            print("⚠️ Audio buffer overflow - clearing queue", file=sys.stderr)
            # Clear the queue to prevent backup
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
        else:
            print(status, file=sys.stderr)
    q.put(bytes(indata))

def record_voice(prompt="🎙 I'm listening, sir..."):
    """
    Blocking call, returns the first recognized sentence.
    Optimized for faster response with aggressive silence detection.
    """
    import time
    print(prompt)
    rec = vosk.KaldiRecognizer(model, 16000)
    rec.SetMaxAlternatives(0)
    rec.SetWords(False)
    
    last_partial = ""
    silence_start = None
    speech_detected = False
    SILENCE_TIMEOUT = 1.2  # Balanced timeout - finalize after 1.2s of silence (was 0.6s - too aggressive)
    
    with sd.RawInputStream(samplerate=16000, blocksize=6000, dtype='int16',  # Increased to reduce overflow
                           channels=1, callback=callback):
        while not stop_listening_flag.is_set():
            try:
                data = q.get(timeout=0.05)
            except queue.Empty:
                # Force finalize if we have speech and silence timeout reached
                if speech_detected and last_partial.strip() and silence_start:
                    if time.time() - silence_start > SILENCE_TIMEOUT:
                        final = json.loads(rec.FinalResult())
                        text = final.get("text", "")
                        if text.strip():
                            print("👤 You:", text)
                            return text
                        # If FinalResult empty, use last partial
                        if last_partial.strip():
                            print("👤 You:", last_partial)
                            return last_partial
                continue
            
            # Process audio
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text.strip():
                    print("👤 You:", text)
                    return text
            
            # Monitor partial results for faster detection
            partial = json.loads(rec.PartialResult())
            current_partial = partial.get("partial", "")
            
            if current_partial:
                speech_detected = True
                if current_partial != last_partial:
                    last_partial = current_partial
                    silence_start = time.time()  # Reset timer on new words
                elif not silence_start:
                    silence_start = time.time()  # Start timer on same partial
                    
    return ""
