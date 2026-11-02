"""Makes the four 16 kHz mono clips for the YAMNet runs.   prep_sounds.py CLIPS_DIR OUT_DIR
dog.ogg, clap.oga, whistle.ogg come from Wikimedia Commons (see data/SOURCES.md); speech is the Gettysburg head clip."""
import sys
import numpy as np, soundfile as sf
from prep_audio import to16k   # noqa  (prep_audio only runs its job under __main__)

src, out = sys.argv[1], sys.argv[2]
for name, f in [("dog", "dog.ogg"), ("clap", "clap.oga"), ("whistle", "whistle_pcm.wav"), ("speech", "gettysburg_head.ogg")]:
    x, sr = sf.read(f"{src}/{f}", dtype="float32"); y = to16k(x, sr)[: 16000 * 12]
    y = y / max(1.0, float(np.abs(y).max()))   # the resampler can overshoot a clipped clip
    sf.write(f"{out}/{name}.wav", y, 16000, subtype="PCM_16"); print(name, sr, round(len(y) / 16000, 2), "s, peak", float(np.abs(y).max()))
