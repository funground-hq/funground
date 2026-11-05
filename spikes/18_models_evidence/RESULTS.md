# Spike 18: models evidence for release 0.2 (S-250 YAMNet, S-234 Whisper)

Branch: `cloud/models-evidence` (the name the task gave; the session accepted it). Cloud session, Linux x86-64, 4 vCPUs
(Intel Xeon @ 2.80 GHz), 16 GB. Started 2026-11-05 07:26 UTC. Nothing in `funground/` or `ml/` was changed, and funground itself
was not installed (no core tests were run, because no code under test changed). Two separate venvs (uv, Python 3.11.18):

- `venv_y` (YAMNet): tensorflow-cpu 2.15.1, tensorflow-hub 0.16.1, tf2onnx 1.16.1, onnx 1.17.0, onnxruntime 1.26.0,
  numpy 1.26.4, protobuf 3.20.3, scipy (resample_poly), soundfile.
- `venv_w` (Whisper): onnxruntime 1.31.1 (the version spike 16 used), tokenizers 0.23.3, numpy 2.4.6, scipy 1.17.1, soundfile 0.14.0, jiwer 4.0.0, pyarrow.

`ORT_DISABLE_TELEMETRY=1`, `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` throughout. Datasets, audio and model files stayed in the
session scratch area and are not committed; the URLs, revisions and SHA-256 below identify them.

Scripts here: `yamnet_compare.py`, `yamnet_analyse.py`, `yamnet_analyse_clean.py`, `yamnet_learner.py`, `convert_yamnet.sh`,
`onnx_diff.py`; `make_manifest.py`, `fetch_edacc.py`, `whisper_eval.py`, `whisper_analyse.py`, `whisper_rtf.py`.
Results: `yamnet_summary.json`, `yamnet_learner.json`, `whisper_summary.json`, `whisper_rtf_*.json`.

---

## Part 1: YAMNet (S-250)

### 1.1 Google's model

| What | Value |
|---|---|
| Source | Kaggle Models `google/yamnet`, framework TensorFlow 2, variation `yamnet`, version 1 (the TF Hub URL `https://tfhub.dev/google/yamnet/1?tf-hub-format=compressed` redirects to `https://storage.googleapis.com/kaggle-models-data/629/762/bundle/archive.tar.gz`) |
| Kaggle record | author Google, published 2020-10-06, updated 2023-01-11; licence of every instance: **Apache 2.0** (Kaggle API `models/google/yamnet/get`) |
| Archive | 14,242,921 bytes, SHA-256 `b80da2a1a56926fb0767205051a200dd7b3beaf3ea1ea126c42a53943996e5e0` |
| `saved_model.pb` | 3,176,321 bytes, `672af6e1e34fe15a42d45d70217fd39f97e10aef9b0effbf9b0bf7826fccd462` |
| `variables.data-00000-of-00001` | 15,077,564 bytes, `d6753f22f173b2a8b1ce78918eaae79bf0a41ca61f4cfe9a1b948c97ff094ddc` |
| `variables.index` | 7,400 bytes, `0bc2ca10e56e8a71b96a2cad26adbbabff927e9344fbd2df8ae7275ddf76ae1e` |
| `assets/yamnet_class_map.csv` | `cdf24d193e196d9e95912a2667051ae203e92a2ba09449218ccb40ef787c6df2`: **identical** to the community repo's class map |

The fall-back (tensorflow/models `research/audioset/yamnet` with `yamnet.h5`) was not needed. That repository is Apache 2.0 too
(its `LICENSE`, fetched).

### 1.2 Audio

- **ESC-50**: `github.com/karolpiczak/ESC-50` at commit `33c8ce9eb2cf0b1c2f8bcf322eb349b6be34dbb6`, **all 2,000 clips**
  (5 s, 44.1 kHz, 50 classes of 40). Licence CC BY-NC (ESC-10 subset CC BY): used to evaluate only, not committed.
  Each clip is resampled to 16 kHz once (scipy `resample_poly(x, 160, 441)`), and the same samples go to every model.
- **Edge cases** (9): silence 1 s and 5 s, an empty array (0 s), 0.1 s and 0.5 s (shorter than one 0.96 s window), exactly
  0.96 s, a clip clipped hard (x20 then limited to ±1), a quiet clip (x0.001), and seeded white noise (seed 18).

### 1.3 Community ONNX against Google's TensorFlow model

Community file: `audiomagic/yamnet-onnx` at `f25b741c2f0bdc6d7e6db24b5fddda23347dbafd`, `yamnet.onnx` 16,093,355 bytes,
`d3835ffb…f908e` (the hash spike 16 recorded: same file). Google's model ran in TensorFlow 2.15.1, the ONNX file in
onnxruntime 1.26.0, both on 1 thread. Command: `yamnet_compare.py` (see its docstring).

| Measure (2,009 clips, 14,346 windows) | Community ONNX | Our tf2onnx conversion |
|---|---|---|
| Errors or crashes (incl. 0 s and 0.1 s input) | 0 | 0 |
| Clips whose window count differs from Google's | **0** | **0** |
| Largest score difference, any window, any class | **6.7e-5** | **6.7e-5** |
| Largest difference in the clip score (mean of windows) | 1.8e-5 | 1.8e-5 |
| Top-1 agreement, by window | **100 %** | **100 %** |
| Top-1 agreement, by clip | **100 %** | **100 %** |
| Top-3 agreement (same 3 names, same order), by clip | 99.6 % raw; **100 %** when ties are excluded | same |
| Top-3 agreement (same 3 names), by window | 89.0 % raw (see note) | same |

Note on top-3. Every raw top-3 difference came from **ties at zero**: on silence Google's model scores "Silence" 1.0 and
the other 520 classes about 0, so the 2nd and 3rd places are decided by rounding noise (Google picks "Music", the ONNX files
"Glockenspiel"). With ties excluded (a difference counts only if Google's 3rd score is at least 0.001) there are
**0** clip-level top-3 differences out of 2,009. A tie-aware window-level count was started late (`compare2.jsonl`); see 1.7.

**Framing and padding match Google's.** Window counts are equal for every clip: 5 s gives 10 windows (0.96 s window, 0.48 s
hop), 1 s gives 2, and anything of 0.96 s or less, including an empty array, gives 1 padded window, in all three models. That
also matches the largest difference: an error in the framing would move scores by far more than 1e-4. Both ONNX files take the
raw 16 kHz waveform (`waveform`, any length) and return scores (n, 521), embeddings (n, 1024) and the log-mel patch (n, 64).

### 1.4 Our own conversion with tf2onnx

Recipe (`convert_yamnet.sh`), on Linux x86-64, Python 3.11.18:

```sh
uv venv --seed --python 3.11 venv_y
venv_y/bin/python -m pip install "tensorflow-cpu==2.15.1" "tf2onnx==1.16.1" "onnx==1.17.0" "numpy<2" onnxruntime soundfile scipy
# resolved: numpy 1.26.4, protobuf 3.20.3, onnxruntime 1.26.0
venv_y/bin/python -I -m tf2onnx.convert --saved-model <unpacked google/yamnet/1> --signature_def serving_default --opset 13 --output yamnet.onnx
```

About 20 s. Results:

| Run | Opset | Bytes | SHA-256 |
|---|---|---|---|
| 1 | 13 | 16,093,501 | `d2e2733ac2ca631113d4aaf70e5ece5346c0ecf6cd4f966c8b172c41b41245a4` |
| 2 | 13 | 16,093,677 | `f2ea289f10e090af3de5ab5943cbcac5abb41852be1c882a9c90578efeaa58ec` |
| 3 (`PYTHONHASHSEED=0`) | 13 | 16,093,414 | `54b1186790c8a9bcfb4b969ff15146d455de8a9430621bde63d28b5d0283f689` |
| 4 (`PYTHONHASHSEED=0`) | 13 | 16,093,459 | `c47b1fabb339020f220eedc35fa0cd118fa44f82e191c55911683fcea6a0bb2b` |
| 5 | 15 | 16,093,449 | `80d9ccfce92a2758fa477d441b3d59b79a81918b6f6b5f7308bfae728144908e` |

**Not byte-for-byte repeatable**, even with a fixed Python hash seed. `onnx_diff.py` shows why: the two files have the same
91 weight tensors (byte-identical as a set), the same 152 nodes with the same op types in the same order and the same node
names. Only the **names of small de-duplicated constants** differ (for example a `Slice` input called `cst0__63` in one run
and `const_starts__11` in the other; 82 of 91 initialisers are byte-identical by name). The behaviour is identical (1.3).

**The community file is almost certainly a plain tf2onnx 1.16.1 conversion of this same model at opset 15**: its producer is
`tf2onnx 1.16.1 15c810`, opset 15, the same 91 weights (byte-identical as a set), the same 152 nodes and node names. Its size
(16,093,355) is within 350 bytes of ours, which is the size range that constant names alone give.

### 1.5 How right is it for a learner?

46 ESC-50 classes that map cleanly to AudioSet names (1,840 clips; mapping in `yamnet_analyse_clean.py`, written before
looking at results; for example dog → "Dog" or "Bark", door_wood_knock → "Knock", clapping → "Clapping"). The 4 left out:
can_opening, drinking_sipping, mouse_click, washing_machine (no clean AudioSet name). Google's model and both ONNX files give
**identical** shares.

| Clip score | Right name is top 1 | Right name in top 3 |
|---|---|---|
| Mean of windows (Google's demo; what spike 16 does) | **24.5 %** | **64.6 %** |
| Max over windows | 24.7 % | 64.1 % |
| Mean, leaving out "Silence" and 26 broad parent names | 58.8 % | 76.7 % |
| Max, the same names left out | 57.7 % | 75.5 % |

Why top 1 is so low. YAMNet names the **parent** before the specific sound: for dog clips the commonest top-1 is "Animal"
(22 of 40), then "Silence" and "Domestic animals, pets"; trains give "Vehicle" (28 of 40) and "Rail transport"; church bells
give "Bell" (39 of 40); crying babies "Crying, sobbing" (34 of 40). ESC-50 clips are 5 s with the sound often lasting under
a second, so "Silence" wins on short sounds (sneezing 35 of 40, door knock 29 of 40, glass breaking 31 of 40). Best classes:
keyboard typing, thunderstorm, toilet flush (above 80 % top 1); worst: door creaks and pouring water (0 % top 3), rooster, hen,
wind, water drops, crackling fire. Per class: `yamnet_summary.json` → `learner.google.per_class`.

**Caveat on the third and fourth rows:** the list of left-out names (`yamnet_learner.py`, `GENERIC`) was written **after**
seeing which top-1 names were common, so the gain is optimistic. It is evidence that a learner-facing helper should skip
"Silence" and parent names, not a measured accuracy; check it on held-out sounds first. The model files are not the problem:
Google's own model gives the same numbers.

### 1.6 Which file to host, and credit

**Host the community file `yamnet.onnx` (SHA-256 `d3835ffbbd4a1bb3e777f0ca217b5007907f5171dd5d17c4236b95b2af8f908e`,
16,093,355 bytes), now checked.** On 2,000 ESC-50 clips and 9 edge cases it equals Google's TensorFlow model to 6.7e-5 on every
window and class, with the same framing and 100 % top-1 agreement. Its structure shows it is tf2onnx 1.16.1 of Google's
model. Our own conversion is equally faithful but gives no advantage: tf2onnx does not repeat byte for byte, so "rebuild it and
compare hashes" is not possible either way. The hash we keep is what identifies the file. If the maintainer prefers a file whose
whole history we own, host conversion run 1 (`d2e2733a…45a4`, opset 13) and keep `convert_yamnet.sh` with `yamnet_compare.py`
as the check. Equivalence is then shown by scores, not by hash. Either way, mirror `yamnet_class_map.csv` (`cdf24d19…6df2`)
beside it.

Licences: the model is Apache 2.0 (Google; Kaggle `google/yamnet` and tensorflow/models). The community repo is Apache 2.0
(spike 16). The 521 class names are the **AudioSet ontology**, by Google, under **CC BY 4.0**. Suggested credit:

> Sound names from the AudioSet ontology by Google LLC (research.google.com/audioset), licensed under CC BY 4.0
> (creativecommons.org/licenses/by/4.0). YAMNet model by Google LLC, Apache License 2.0.

The citation Google asks for AudioSet is Gemmeke et al., "Audio Set: An ontology and human-labeled dataset for audio events",
ICASSP 2017. The exact wording Google prefers was not re-checked here (unverified).

### 1.7 Not done or partial (YAMNet)

- Tie-aware window-level top-3, and the second conversion run in the full comparison: `compare2.jsonl` was started at low
  priority late in the session. The count reached is in "For the main session".
- Browser timing (onnxruntime-web) was not re-measured; spike 16's numbers stand.
- A live microphone and noisy rooms were not tested for YAMNet.
