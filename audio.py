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


def generate_division_tone(duration_ms=50, frequency=2000, sample_rate=44100):
    """Generate a division tick tone (1 octave up, half duration, half volume).
    
    Args:
        duration_ms: Duration in milliseconds
        frequency: Frequency in Hz (typically double the beat tone for 1 octave up)
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
    
    return (tone * envelope * 0.6).astype(np.float32)  # Half volume


def generate_beat_pattern(divisions=1, click_duration_ms=50, beat_frequency=2000, 
                          division_frequency=1000, sample_rate=44100, bpm=120):
    """Generate a complete beat pattern with evenly-spaced clicks.
    
    Creates a single audio buffer containing clicks spaced evenly across one beat duration.
    The first click is the beat (beat_frequency), and remaining clicks are divisions (division_frequency).
    
    Args:
        divisions: Number of total clicks per beat (1 for beat only, 2+ for beat + divisions)
        click_duration_ms: Duration of each individual click
        beat_frequency: Frequency of the beat click in Hz
        division_frequency: Frequency of division clicks in Hz
        sample_rate: Sample rate in Hz
        bpm: Beats per minute (used to calculate actual beat duration)
    
    Returns:
        numpy array of audio samples for the entire beat pattern
    """
    click_samples = int(sample_rate * click_duration_ms / 1000)
    
    # Generate click tone templates
    t = np.linspace(0, click_duration_ms / 1000, click_samples)
    
    # Envelope for clicks: quick attack, linear decay
    envelope = np.ones(click_samples)
    decay_start = int(click_samples * 0.8)
    envelope[decay_start:] = np.linspace(1, 0, click_samples - decay_start)
    
    # Beat click
    beat_tone = np.sin(2 * np.pi * beat_frequency * t).astype(np.float32) * envelope * 0.8
    
    # Division click (lower pitch, same duration, 30% lower volume)
    div_tone = np.sin(2 * np.pi * division_frequency * t).astype(np.float32) * envelope * 0.4
    
    # Calculate actual beat duration from BPM
    # At MIDI_PPQN=24, one beat = 24 clock ticks
    # Beat duration = (60 / BPM) seconds = (60000 / BPM) milliseconds
    beat_duration_ms = 60000 / bpm
    total_samples = int(sample_rate * beat_duration_ms / 1000)
    
    pattern = np.zeros(total_samples, dtype=np.float32)
    
    # Place clicks evenly across the beat
    for i in range(divisions):
        # Calculate position proportionally
        position_ratio = i / divisions
        start_sample = int(position_ratio * total_samples)
        end_sample = min(start_sample + click_samples, total_samples)
        
        # Ensure we don't go out of bounds
        if start_sample < total_samples:
            samples_available = end_sample - start_sample
            
            # Choose tone: beat for position 0, division for others
            tone = beat_tone if i == 0 else div_tone
            pattern[start_sample:end_sample] = tone[:samples_available]
    
    return pattern


def play_click(tone):
    """Play a click tone immediately (non-blocking).
    
    Args:
        tone: numpy array of audio samples
    """
    if tone is None or len(tone) == 0:
        return
    sd.play(tone, samplerate=44100, blocking=False)
    sd.play(tone, blocking=False)

