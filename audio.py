"""Simple tone generator for metronome clicks."""

import numpy as np
import sounddevice as sd


def generate_click_tone(duration_ms=100, frequency=1000, sample_rate=44100):
    """Generate a simple sine wave click tone.
    
    Args:
        duration_ms: Duration in milliseconds
        frequency: Frequency in Hz
        sample_rate: Sample rate in Hz
    
    Returns:
        numpy array of audio samples (float32, normalized to [-1, 1])
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, num_samples)
    
    # Simple sine wave with fast attack/release envelope
    tone = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    # Envelope: quick attack, linear decay
    envelope = np.ones(num_samples)
    decay_start = int(num_samples * 0.8)
    envelope[decay_start:] = np.linspace(1, 0, num_samples - decay_start)
    
    return (tone * envelope * 0.8).astype(np.float32)


def play_click(tone):
    """Play a click tone immediately (non-blocking).
    
    Args:
        tone: numpy array of audio samples
    """
    sd.play(tone, blocking=False)
