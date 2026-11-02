"""Makes the 16 kHz mono clips used on both platforms. Run with the scratch venv's python (-I is fine).
    prep_audio.py CLIPS_DIR OUT_DIR
Reads tts_raw.wav and gettysburg_head.ogg from CLIPS_DIR; writes tts.wav and gettysburg.wav to OUT_DIR."""
import sys
import numpy as np, soundfile as sf


def to16k(x, sr):
    if x.ndim > 1: x = x.mean(axis=1)
    n_out = round(len(x) * 16000 / sr)
    X = np.fft.rfft(x)
    Y = np.zeros(n_out // 2 + 1, complex); k = min(len(X), len(Y)); Y[:k] = X[:k]
    return (np.fft.irfft(Y, n_out) * n_out / len(x)).astype(np.float32)


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    x, sr = sf.read(f"{src}/tts_raw.wav", dtype="float32"); y = to16k(x, sr); print("tts", sr, len(y) / 16000)
    sf.write(f"{out}/tts.wav", y, 16000, subtype="PCM_16")
    x, sr = sf.read(f"{src}/gettysburg_head.ogg", dtype="float32"); y = to16k(x, sr)[: 16000 * 12]; print("gettysburg", sr, len(y) / 16000)
    sf.write(f"{out}/gettysburg.wav", y, 16000, subtype="PCM_16")
