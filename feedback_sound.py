# feedback_sound.py
import numpy as np
import sounddevice as sd
import os


def play_ding():
    """Play a quick 'ding' sound for immediate feedback."""
    try:
        # Generate a pleasant notification sound (C5 note)
        duration = 0.15  # seconds
        frequency = 523.25  # C5 (Do)
        sample_rate = 44100
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Create a note with harmonics for richer sound
        note = np.sin(frequency * 2 * np.pi * t)  # fundamental
        note += 0.3 * np.sin(frequency * 4 * np.pi * t)  # 2nd harmonic
        note += 0.15 * np.sin(frequency * 6 * np.pi * t)  # 3rd harmonic
        
        # Apply envelope (fade in/out) for smooth sound
        envelope = np.ones_like(t)
        fade_samples = int(0.01 * sample_rate)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        note = note * envelope * 0.2  # Volume 20%
        
        # Play asynchronously
        sd.play(note, sample_rate, blocking=False)
        
    except Exception as e:
        print(f"Ding sound error: {e}")


def play_error_sound():
    """Play a low tone for errors."""
    try:
        duration = 0.2
        frequency = 220  # A3 (La basso)
        sample_rate = 44100
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        note = np.sin(frequency * 2 * np.pi * t) * 0.15
        
        # Quick fade out
        envelope = np.linspace(1, 0, len(t))
        note = note * envelope
        
        sd.play(note, sample_rate, blocking=False)
        
    except Exception as e:
        print(f"Error sound error: {e}")
