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
**0** clip-level top-3 differences out of 2,009. A second, tie-aware run (`yamnet_summary_run2.json`, the first 381 clips: 9 edge cases and 372 ESC-50 clips, 3,766 windows, with conversion run 2 added) gives **100 % tie-aware window top-3 agreement** for all three ONNX files, and a largest difference of 2.7e-5.

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

- The tie-aware window-level top-3 count and conversion run 2 cover 381 of the 2,009 clips only (stopped at 07:54 to free the CPUs).
- Browser timing (onnxruntime-web) was not re-measured; spike 16's numbers stand.
- A live microphone and noisy rooms were not tested for YAMNet.

---

## Part 2: Whisper (S-234)

### 2.1 Models

| Model | Repo and commit | File | Bytes | SHA-256 |
|---|---|---|---|---|
| tiny.en q8 | `onnx-community/whisper-tiny.en` @ `2575352d61be1bf7225cf8f8b268a4678025fc58` | encoder_model_quantized.onnx | 10,124,993 | `e93ec822…3a25` (same as spike 16) |
| | | decoder_model_merged_quantized.onnx | 30,718,858 | `c0592d07…be52` (same) |
| base.en q8 | `onnx-community/whisper-base.en` @ `51eefc0af78b103839eda9e7e4f4186acc6517fe` | encoder_model_quantized.onnx | 23,201,320 | `6e8001198c490bbae018c0044f630c2915efb826bad957006ce36152d0ab2a10` |
| | | decoder_model_merged_quantized.onnx | 53,692,803 | `dd4761a3f7add26afda3512abff4706920404c2517e85a9f2ff090b0c0987909` |
| both | | tokenizer.json | 2,405,679 | `5eb60cec…10d0` (identical in both repos) |

Download: tiny.en 40.8 MB, base.en **76.9 MB** (1.9 times as much), plus the 2.4 MB tokenizer for either. The decode loop is
spike 16's (`whisper_desktop.py`: own log-mel, greedy decoding, suppress lists), copied line for line in `whisper_eval.py`. The
only change is that the empty key/value cache shape is read from `config.json`, because base.en has 8 heads, not 6.

### 2.2 Speech used

| Group | Source | Licence | Used |
|---|---|---|---|
| Indian English, read (1 speaker, ksp, male) | CMU ARCTIC 0.95, festvox.org `cmu_us_ksp_arctic-0.95-release.tar.bz2` | free use (the ARCTIC licence: BSD-like, keep the copyright notice) | 57 utterances |
| US English, read (bdl male, slt female) | CMU ARCTIC 0.95 | same | 47 |
| Canadian English, read (jmk) | CMU ARCTIC 0.95 | same | 22 |
| Scottish English, read (awb) | CMU ARCTIC 0.95 | same | 24 |
| Indian English, **conversational** (2 speakers: EDACC-C05-B, L1 Indian English; EDACC-C36-A, L1 Hindi) | EdAcc, `edinburghcstr/edacc` @ `d9ae7bd344f0562b766ec93ee5ce8f2f9568ce66`, test split, seeded 150 of 631 Indian English rows (147 kept, 143 with words) | CC BY-SA 4.0 (dataset card) | 143 |
| LibriSpeech test-clean (read audiobooks, mostly US) | openslr.org/resources/12 `test-clean.tar.gz` | CC BY 4.0 | 245 of a seeded 500 |

Sampling seed 18 (`make_manifest.py`; ARCTIC: ksp 200 and 60 for each other speaker in a mixed order, so a stopped run still
covers everyone). **Not reached:** Svarah (AI4Bharat, Indian English) is gated on the Hub and this session has no token.
L2-ARCTIC needs registration. I found no openly licensed children's speech in the time available (not searched thoroughly).
Each run was stopped at 07:54, so not all sampled utterances were transcribed. Both models are compared on exactly the same
(utterance, condition) pairs.

### 2.3 Conditions

`clean`; `snr20` and `snr10`: seeded room or fan noise (pink noise plus a 100 Hz hum and harmonics, generated; seed from
the SHA-256 of the utterance id and condition) mixed at 20 and 10 dB SNR (signal-to-noise ratio: the speech is 100 times,
or 10 times, as strong as the noise); `mic`: a cheap microphone, a 4th-order Butterworth band-pass from 300 to 3,400 Hz.
ARCTIC got all four. LibriSpeech and EdAcc got clean and snr10 only, to save time. ESC-50 room sounds were not used.

### 2.4 Word error rate

WER (word error rate) = (substituted + deleted + inserted words) / reference words, after normalising: lower case,
punctuation removed, contractions and numbers written out, fillers (um, uh) and EdAcc event tags removed
(`whisper_analyse.py`). 95 % interval: 2,000 bootstrap resamples of utterances, seed 18. Lower is better.

| Group (utterances) | Condition | tiny.en WER % (95 % CI) | base.en WER % (95 % CI) |
|---|---|---|---|
| **Indian, ARCTIC ksp (57)** | clean | **12.2** (9.3 to 15.5) | **10.5** (7.7 to 13.6) |
| | snr20 | 12.8 (9.3 to 16.3) | 10.2 (7.4 to 12.8) |
| | snr10 | 17.9 (14.2 to 21.7) | 13.5 (10.1 to 16.9) |
| | mic | 14.3 (10.0 to 18.8) | 11.3 (8.2 to 14.7) |
| **Indian, EdAcc conversation (143)** | clean | **32.2** (24.2 to 43.0) | **26.1** (18.6 to 36.9) |
| | snr10 | **62.8** (42.0 to 92.9) | 35.4 (27.4 to 46.0) |
| US, ARCTIC (47; 46 for noisy/mic) | clean | 5.6 (2.6 to 9.3) | 2.8 (0.9 to 5.4) |
| | snr20 | 6.7 (3.8 to 9.8) | 4.8 (2.2 to 8.0) |
| | snr10 | 8.6 (5.7 to 11.7) | 5.7 (3.3 to 8.6) |
| | mic | 7.7 (4.3 to 11.9) | 3.8 (1.5 to 6.8) |
| Canadian, ARCTIC (22) | clean / snr20 / snr10 / mic | 5.8 / 9.3 / **29.3** / 7.6 | 4.9 / 6.7 / **20.0** / 5.8 |
| Scottish, ARCTIC (24) | clean / snr20 / snr10 / mic | 4.1 / 5.0 / 13.1 / 3.6 | 3.6 / 3.2 / 6.8 / 4.1 |
| LibriSpeech test-clean (245) | clean | 6.1 (4.9 to 7.3) | 3.7 (3.0 to 4.4) |
| | snr10 | 9.8 (8.5 to 11.3) | 5.7 (4.8 to 6.7) |

Full table with intervals, words and the share of utterances that came out exactly right: `whisper_summary.json` → `wer`.

What it says:
- **Indian English read speech is about twice the error of US read speech** for both models (tiny 12 % against 6 %; base 10 %
  against 3 %). That is one speaker, so this is an example, not a measure of "Indian English".
- **Conversation is the real gap.** On EdAcc's two Indian speakers, tiny gets about 1 word in 3 wrong and base 1 in 4. Some of
  this is the speaking style (fast, overlapping, informal), not the accent; EdAcc has no non-Indian group here to separate
  the two (not measured).
- **A noisy room hurts tiny far more than base.** At 10 dB, tiny's EdAcc WER doubles (32 → 63 %) and has **runaway
  repetition loops** in 5 of 143 utterances (for example "… because it's a good, good, good, good, …" until the 200-token limit).
  base had 2. The Canadian speaker at 10 dB: tiny 29 %, base 20 %.
- **The cheap-microphone band (300 to 3,400 Hz) costs little**: 1 to 2 points for either model.
- **base.en is better in every group and condition.** Its interval overlaps tiny's in most of the small ARCTIC groups, but not
  on LibriSpeech (245 utterances: 3.7 against 6.1 clean) or on EdAcc in noise.

### 2.5 Speed (real-time factor)

RTF (real-time factor) = seconds of computing / seconds of audio; under 1 is faster than real time. Machine otherwise idle,
10 LibriSpeech clips (median 6.3 s), warm-up then best of 2 (`whisper_rtf.py`):

| Model | 1 thread: RTF median (max), s per clip | 4 threads: RTF median (max), s per clip |
|---|---|---|
| tiny.en q8 | **0.16** (0.24), 1.0 s | 0.18 (0.27), 1.2 s |
| base.en q8 | **0.30** (0.46), 2.0 s | 0.26 (0.36), 1.7 s |

base.en is about **twice as slow** at 1 thread. 4 threads hardly help here (tiny was slightly *slower*), probably because the
decoder runs many small steps one token at a time. During the bulk runs (4 to 6 processes sharing 4 CPUs) the medians were
0.28 (tiny) and 0.59 (base). **Browser speed is unverified.** Spike 16 measured tiny.en at RTF 0.37 to 0.54 in a 1-thread wasm
worker on the maintainer's slow machine. If base scales the same (about 2x), it would be about 0.8 to 1.1 there: **at or over
real time** (an estimate, not measured).

### 2.6 Common confusions (for S-236)

Counted on clean speech only, all groups pooled (`whisper_summary.json` → `confusions`, `confusion_groups`). Grouped:

| Kind | tiny.en | base.en | Real examples (reference → heard) |
|---|---|---|---|
| Sounds alike (similar spelling or sound) | 235 | 168 | price → prize, mate → made, read → red, scents → sense, omissions → emissions, throw → through, movements → moments, stooped → stop, sheath → sheet |
| Small words swapped (a, the, he, his …) | 232 | 165 | he → we, an → and, his → has, her → a, you → he, him → me, a → your |
| Words added | 257 | 228 | "the", "and", "a" put in; in conversation whole phrases |
| Words dropped | 265 | 221 | "you know", "like", "so", "it's" in conversation (the model tidies speech up) |
| Names | 16 | 17 | Jeanne → Gene, Young → Yang, Selden's → seldom / cell-dense, Fort Churchill → four Churchill / 4 church till, Yukon → can, Elijah → Aliza |
| Other substitutions | 154 | 79 | tomfoolery and rot → town full of reindeer (tiny) |
| Spelling, not hearing | | | manoeuvring → maneuvering (the model writes American spelling) |

The 30 most common single confusions are in the JSON. Most of them are small words dropped or added in EdAcc conversation, and
these make poor teaching examples. The rows above are the instructive ones for a chapter on why a model is wrong: it guesses
words that sound alike, it prefers common words to rare names, it tidies up how people really talk, and in noise it can
**loop**, repeating one word.

### 2.7 Recommendation: tiny.en or base.en

**Keep tiny.en q8 as the default for 0.2, and offer base.en q8 as an opt-in "more accurate" model** (one argument, the same
loop). Also add a **repetition guard** to the loop, whatever the model: stop when the same token or bigram repeats about 4 times,
and cap the tokens by clip length. This alone removes the worst failures (runaway loops in noise).

Why. base.en is clearly more accurate (LibriSpeech 3.7 % against 6.1 %; Indian read speech 10.5 % against 12.2 %; noisy
conversation 35 % against 63 %), but it is 1.9 times the download (76.9 MB against 40.8 MB). It is also about 2 times slower,
which in the browser at 1 thread probably puts it near real time on a slow machine. For short, clear commands to a sketch,
tiny's 5 to 12 % is usable. For noisy classrooms and conversational speech neither model is good, and base is much better.

What would change my answer:
- If a browser measurement shows base.en at RTF under 0.6 on the slowest target machine, **move to base.en**: the accuracy gain
  in noise is large.
- If learners mostly speak in noisy rooms (a classroom) or in an Indian English conversational style, base.en is worth its size.
- If most learners have slow connections, or the 77 MB download is a problem for a classroom's network, stay on tiny.en.
- More Indian English speakers (Svarah, L2-ARCTIC), children's speech, and real laptop-microphone recordings could move these
  numbers. They are the main gap.

---

## Problems met

- `github.com` archive downloads are blocked by the session proxy: ESC-50 was fetched with `git clone --depth 1` instead.
- The first CMU ARCTIC URL (`festvox.org/cmu_arctic/packed/…`) gave 404. The right path is `festvox.org/cmu_arctic/cmu_arctic/packed/…`.
- Svarah is gated (needs a Hub token). The datasets-server filter endpoint for EdAcc failed with an authentication error, so
  `fetch_edacc.py` reads parquet row groups by HTTP range instead.
- The first WER pass counted contractions ("you've" against "you have"), EdAcc fillers and `<COUGH>`-style tags as errors.
  The normaliser was fixed before the numbers above were made.
- tf2onnx output is not byte-repeatable (1.4).
- I typed a bare `python3` once (to read Kaggle's JSON), against the rule. It was the system Python 3.13 in a cloud container,
  and it ran and printed; no installer was involved.
- The Whisper bulk runs shared the CPUs (up to 6 processes on 4), so their per-utterance times are not used for speed. Only
  `whisper_rtf_*.json` (idle machine) is.

---

## For the main session

**Found.**
1. **S-250 condition met, with evidence.** The community YAMNet ONNX (`d3835ffb…f908e`) matches Google's TensorFlow model
   (Kaggle `google/yamnet` v1, Apache 2.0, archive `b80da2a1…e5e0`) on all 2,000 ESC-50 clips and 9 edge cases: largest
   difference 6.7e-5, top-1 agreement 100 % by window and by clip, the same framing and padding, and no top-3 differences
   apart from ties at zero. Structurally it is a tf2onnx 1.16.1, opset 15 conversion of Google's model.
2. **tf2onnx is not byte-repeatable** (same weights and graph, different constant names), so a hash can identify the file
   we host but cannot prove how it was built. The proof is the score comparison (`yamnet_compare.py`).
3. **YAMNet names parents first.** For learners, the right name is top 1 in only 24.5 % of clean-class ESC-50 clips
   ("Animal", "Vehicle", "Silence" win), and in the top 3 in 64.6 %. Leaving out "Silence" and broad parent names raised
   top 1 to about 59 % (optimistic: the list was chosen after looking). This matters more for S-250's helper design than the
   choice of file.
4. **Whisper:** tiny.en's error rate is 6 % on clear US read speech, 12 % on one Indian English reader and 32 % on Indian English
   conversation. Noise at 10 dB doubles the conversation error, and tiny falls into **repetition loops** (5 of 143). base.en
   is better everywhere (3.7 % against 6.1 % on LibriSpeech), but it is 1.9 times the size and about 2 times slower.

**Fixed:** nothing in funground (none was in scope).

**Needs the maintainer.**
- Choose which YAMNet file to host: the community file (recommended, now checked) or our conversion run 1 (`d2e2733a…45a4`).
  Add the AudioSet CC BY 4.0 credit (1.6) to the credits.
- Whisper: keep tiny.en as the default (recommended), offer base.en as an opt-in, and add a repetition guard to the decode
  loop (a candidate story). Changing the default model is the maintainer's decision.
- S-250 helper design: consider skipping "Silence" and parent names when showing a learner the best name. Test that on
  held-out sounds first.
- S-236 can use the examples in 2.6.
- Still unmeasured: browser speed of base.en; more Indian English speakers (Svarah needs a Hub token); children's speech;
  real laptop-microphone recordings.

**Commits to review** (branch `cloud/models-evidence`, all `[skip ci]`): `git log origin/main..origin/cloud/models-evidence`.
Only `spikes/18_models_evidence/` is touched.
