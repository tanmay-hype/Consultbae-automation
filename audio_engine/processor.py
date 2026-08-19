# audio_engine/processor.py
import os
import numpy as np
import soundfile as sf
import librosa
from typing import Dict, Any

def analyze_audio_file(file_path: str) -> Dict[str, Any]:
    """
    Extracts physical DSP audio metrics and estimates Signal-to-Noise Ratio (SNR).
    """
    file_size_bytes = os.path.getsize(file_path)
    
    # Read audio array and native sampling rate
    y, sr = librosa.load(file_path, sr=None, mono=True)
    
    # 1. Duration in seconds
    duration = float(librosa.get_duration(y=y, sr=sr))
    
    # 2. Sample Rate in kHz
    sample_rate_khz = round(sr / 1000.0, 2)
    
    # 3. Bitrate calculation in kbps
    bitrate_kbps = round((file_size_bytes * 8) / (duration * 1000.0), 2) if duration > 0 else 0.0
    
    # 4. Loudness in dBFS (RMS Amplitude)
    rms = np.sqrt(np.mean(y**2))
    loudness_db = round(float(20 * np.log10(rms)) if rms > 0 else -100.0, 2)
    
    # 5. SNR & Noise Floor Quality Estimate (Bonus)
    # Segment audio into 50ms frames to isolate speech vs background noise
    frame_length = int(sr * 0.05)
    hop_length = int(sr * 0.025)
    frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length)
    frame_rms = np.sqrt(np.mean(frames**2, axis=0))
    
    frame_rms_clean = frame_rms[frame_rms > 1e-6]
    if len(frame_rms_clean) > 0:
        noise_floor_rms = np.percentile(frame_rms_clean, 10)
        signal_rms = np.percentile(frame_rms_clean, 90)
        snr = round(float(20 * np.log10(signal_rms / noise_floor_rms)), 2) if noise_floor_rms > 0 else 40.0
    else:
        snr = 0.0
        
    quality_flag = "Excellent" if snr > 20 else ("Acceptable" if snr > 10 else "High Noise")

    return {
        "duration_seconds": round(duration, 2),
        "sample_rate_khz": sample_rate_khz,
        "bitrate_kbps": bitrate_kbps,
        "loudness_db": loudness_db,
        "snr_db": snr,
        "quality_flag": quality_flag
    }