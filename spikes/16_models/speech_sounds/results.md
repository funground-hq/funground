# S-231 speech, sounds, and a model the learner teaches

Measured 2 Nov 2026 on the maintainer's slow Windows 11 machine. Desktop: onnxruntime 1.31.1, Python 3.14 (scratch venv),
`ORT_DISABLE_TELEMETRY=1`. Web: onnxruntime-web **1.30.0** (wasm, 1 thread, no cross-origin isolation) in a module worker in
headless Chrome 156 (Playwright, temporary profile). Models and pictures came from `127.0.0.1`; the only other host contacted
was `cdn.jsdelivr.net` (3 requests: `ort.wasm.mjs`, the simd-threaded `.mjs` and `.wasm`, 3.2 MB in total). One 404 (not
traced; probably the page's favicon). Every number below is one run on one machine; Whisper times are the best of 3 runs,
YAMNet times the median of 5 to 20.

Files: `whisper_desktop.py`, `whisper_web.js`, `yamnet_desktop.py`, `yamnet_web.js`, `worker.js`, `page.html`, `measure_web.mjs`,
`knn_teach.py`, `make_pooled.py`, `prep_audio.py`, `prep_sounds.py`, `fetch_photos.py`, `compare.py`; results in
`whisper_desktop.jsonl`, `web_whisper.json`, `yamnet_desktop.jsonl`, `web_yamnet.json`, `compare.json`, `knn_results.json`,
`knn_sources.json`; test clips and their sources in `data/`.

## 1. Speech to words: Whisper tiny.en q8

Files: `onnx-community/whisper-tiny.en` at commit `2575352d61be1bf7225cf8f8b268a4678025fc58`.

| File | Bytes | SHA-256 |
|---|---|---|
| `onnx/encoder_model_quantized.onnx` | 10,124,993 | `e93ec822f16a8fd264e7de972ad17d615ea7334b75a52d54c50c2e18dd503a25` |
| `onnx/decoder_model_merged_quantized.onnx` | 30,718,858 | `c0592d0749413c960569e1c7fb806b060d5d18f3ebad4a95cbf9a77dc6e9be52` |
| `tokenizer.json` (not for the web page's model count; 2.4 MB) | 2,405,679 | `5eb60cec1e77aeeb6869a2bb5a8e01a84c3fe5d072d75369343021fe6f5310d0` |

| Measure | Desktop | Web (worker, wasm, 1 thread) | How |
|---|---|---|---|
| Real-time factor, synthesized clip (7.2 s) | **0.12** (0.9 s) | **0.54** (3.9 s) | log-mel + encoder + greedy decode, best of 3 |
| Real-time factor, human clip (12 s) | **0.11** (1.35 s) | **0.37** (4.4 s) | same |
| First load | 0.5 s (create 2 sessions + tokenizer) | 3.5 s from localhost (40.8 MB read + 2 sessions) plus 0.2 s for the library import; from the real Hub the download is extra | page-measured |
| First run against best of 3 | 0.126 against 0.122 | slower first run: see `run_s` in `web_whisper.json` | |
| Word error, synthesized clip | **0 %** (0 of 24 words) | **0 %** | reference = the spoken sentence |
| Word error, human clip | 13 % (3 of 23: "LibriVox" written "LibraVox") | 13 %, same words | reference = LibriVox notice (see `data/SOURCES.md`) |
| Same text on both platforms | synthesized clip: identical string. Human clip: same words, one capital differs ("LibraVox.org." against "libravox.org.") | | `compare.json` |
| Glue code we own | Python 86 lines (log-mel 25, decode loop 25, rest load/CLI) | JS 94 lines (own log-mel by direct DFT, own byte-level token decoding, decode loop) | `wc -l`; `tokenizers` does the decoding on the desktop |

Notes. The web mel is a plain DFT in JS, with an optimisation (frames after the audio are all silence and computed once); the
desktop uses numpy's FFT. I wrote the loop myself on both sides, not Transformers.js, to keep the two the same; the web side
needed about 40 lines more for the tokenizer and the FFT-less mel. q8 here is the `_quantized` (uint8) file; `onnxruntime-web`
1.30.0 ran it without trouble. Models were loaded whole into memory (about 41 MB).

Licence: the Hub card of `onnx-community/whisper-tiny.en` has no licence field; the original `openai/whisper-tiny.en` is Apache-2.0 (card) /
MIT (OpenAI repo). `onnxruntime` MIT, `tokenizers` Apache-2.0. Download 40.8 MB for the two models plus 2.4 MB tokenizer.
Runs in Play's worker, no page needed (it ran in a worker here). Not measured: the Hub as the source (files came from localhost); base.en (not needed).

**Pass:** RTF < 1 on desktop **yes** (0.12); on web **yes** (0.54, but with margin of only 2x on this machine at 1 thread);
word error <= 10 % on the synthesized clip **yes** (0 %); same words on both **yes**. **PASS.**

**Recommendation.** Ship tiny.en q8 on both platforms: it is fast enough, small (43 MB with the tokenizer) and exact on a clear
voice. Expect mistakes on names and brand words (the human clip, "LibriVox"). It transcribes a clip, not a live stream: 30 s is the
model's window, so a sketch hears "a sentence after you stop", not words as you speak. Keep the loop in one shared design
(mel, loop, token decoding are about 90 lines on each side) and test that both agree on the same clip. Not tried: base.en, a noisy
microphone, accents, and clips near 30 s.

## 2. Sounds: YAMNet ONNX

Chosen: `audiomagic/yamnet-onnx` at commit `f25b741c2f0bdc6d7e6db24b5fddda23347dbafd` (Apache-2.0; card, LICENSE and class names
present). `yamnet.onnx` 16,093,355 bytes, SHA-256 `d3835ffbbd4a1bb3e777f0ca217b5007907f5171dd5d17c4236b95b2af8f908e`;
`yamnet_class_map.csv` 14,096 bytes, `cdf24d19...6df2` (identical to the second repo's copy, 521 names).

Vetting. Uploader `audiomagic` is a small company (Audio Magic) that made it for its own tool, created Aug 2026, 0 downloads, 0 likes:
no track record. The card names the upstream (Google's YAMNet v1, Apache-2.0), the Kaggle archive's SHA-256, the conversion command
(tf2onnx, opset 15, weights unchanged) and its checks. The input is the **raw 16 kHz waveform**, the mel front end is inside
the graph, so there is no feature code to write. I compared it with the independent conversion `zeropointnine/yamnet-onnx`
(commit `ac2ca3bd...`, Apache-2.0, 16,093,603 bytes, no card text beyond the command): **scores identical to 5 decimals
on all four clips**, so two unrelated uploads agree. I did **not** compare against Google's TensorFlow model (no TensorFlow here),
so the weights' faithfulness to Google's original is checked only by two conversions agreeing and by the sensible answers. The labels
(AudioSet ontology) are CC BY 4.0, so credit would be needed. Neither repo is from Google; for shipping, funground should
mirror the file and record the hash, as for other models.

| Clip (16 kHz) | Top 3 (mean over windows), desktop = web | Sensible? |
|---|---|---|
| Dog bark, 2.6 s (CC BY-SA, Amada44) | Dog 0.76, Animal 0.76, Domestic animals/pets 0.74 | yes |
| Clapping, 9.8 s (PD) | Hands 0.32, Explosion 0.26, Slap/smack 0.25 | partly: "Hands" is right; no "Clapping" in the top 3 |
| Whistle, 5.4 s (PD) | Whistling 0.73, Alarm 0.19, Whistle 0.16 | yes |
| Speech, 12 s (LibriVox, PD) | Speech 0.87, Silence 0.13, Speech synthesizer 0.03 | yes |

| Measure | Desktop | Web (worker, wasm, 1 thread) |
|---|---|---|
| One call on a 0.96 s window (15,360 samples) | **1.4 ms** | **13 to 28 ms** (median per clip) |
| Per window inside a clip (hop 0.48 s) | 0.8 to 0.9 ms | 21 to 25 ms |
| Real-time factor (one window per 0.48 s hop) | about 0.002 | about 0.05 |
| First load (library import + 16.1 MB + session) | 0.07 s for the session | 7.7 s from localhost (includes fetching the 4 clips; slower than whisper's 3.5 s, not traced) |
| Desktop against web scores | largest difference over 521 classes: **0.00001** (3 clips 0.0) | |
| Size | 16.1 MB (+ 14 KB names) | |
| Glue we own | Python 49 lines (with the command line), 20 without | JS 22 lines |

Licence: Apache-2.0 weights (Google; both repos), AudioSet labels CC BY 4.0. Runs in Play's worker (it did). AST q8
(90.6 MB per the desk research) was not downloaded.

**Pass:** sensible top 3 on >= 3 of 4 **yes** (3 clearly, clapping partly); faster than real time on both **yes**; agreement
within 0.01 **yes** (1e-5). **PASS**, with the caveat on provenance.

**Recommendation.** Use YAMNet ONNX: 16 MB, raw audio in, about 1 ms a window on the desktop and about 25 ms in the browser, and
the same numbers on both. Mirror the file under funground's control and keep the hash, because the uploader is unknown; ask
upstream-faithfulness to be checked once against TensorFlow's model by someone with TensorFlow. The 1024-number embedding output
is also there for a "teach it a sound" sketch. Labels need credit (CC BY 4.0). Not tried: a live microphone stream, noisy rooms, the
numbers on the slowest machines.

## 3. A model the learner teaches: nearest neighbour on embeddings

Data: 24 photos from Wikimedia Commons, all CC0 or Public domain (`knn_sources.json`), 3 classes by 8: **cat, dog, bird**
(dogs are mostly labradors; the birds are mostly great tits). I looked at all 24 on a contact sheet: the labels are right. The
pictures are not in the repository. Each trial: teach 3 pictures per class (9), test on the other 15; **200 random splits**,
the mean accuracy is reported. Cosine nearest neighbour; k=3 is a majority of 3, ties go to the nearest. "How sure" = the best
class's top similarity minus the runner-up class's.

| Model | Size | Vector | ms per picture (desktop, median of 24) | k=1 accuracy (mean, worst, best split) | k=3 accuracy | How sure: median margin right / wrong (k=1) |
|---|---|---|---|---|---|---|
| **DINOv2-small q8** (CLS token) | 24.4 MB | 384 | **79** | **91.4 %** (80 to 100) | **91.5 %** (73 to 100) | 0.37 / 0.03 |
| MobileNetV4-small fp32, pre-classifier (1280) | 15.1 MB | 1280 | **3.9** | 89.5 % (73 to 100) | 86.7 % (60 to 100) | 0.21 / 0.03 |

Per class (k=1): DINOv2 cat 100 %, bird 87 %, dog 87 %; MobileNetV4 cat 98 %, bird 95 %, dog 76 %. Wrong answers have margins
near 0.03 and right answers about 0.2 to 0.4, so "not sure when the margin is under about 0.1" would catch most mistakes with
either model (a rule of thumb from these 24 pictures; not tested on other pictures).

The pre-classifier vector was made by adding the input of the final Gemm as a second graph output (`make_pooled.py`, the `onnx` package);
it is not a file the Hub offers. The earlier measurement that MobileNetV4's *class scores* are poor embeddings stands; the
*pre-classifier* vector is much better and nearly as accurate as DINOv2 here. The DINOv2 and MobileNetV4 desktop-to-web agreement (cosine 0.988
and 0.99998) is from `../onnx/results.md`; I did not re-run the web side.

Licence: DINOv2 weights Apache-2.0; MobileNetV4 (timm weights) Apache-2.0; both from `onnx-community` repos. Runs in Play's
worker (web speed measured earlier: DINOv2 q8 about 0.5 s, MobileNetV4 about 35 ms per picture).

**Pass:** >= 85 % for the chosen model **yes**: DINOv2 91 % (k=1 or 3); MobileNetV4 also passes (89.5 % at k=1,
86.7 % at k=3). **PASS.** Caveats: 24 pictures and three easy, very different classes; a single "taught" set of 3 per
class varies a lot (80 to 100 % between splits), so a learner with 3 examples will see swings.

**Recommendation.** Offer a `teach / guess` helper on picture embeddings with plain k=1 cosine and show the margin as "how sure".
Use MobileNetV4's pre-classifier vector where speed matters (live camera: 4 ms desktop, about 35 ms web) and DINOv2 where the
learner's classes are subtle (79 ms desktop, 0.5 s web, "add an example" speed). MobileNetV4 needs a derived ONNX file we would
host ourselves (one extra output). Not tried: more or harder classes, few-pixel differences, other lighting, and a web run of
the pooled MobileNetV4 vector.

## Problems met

- Commons has no CC0 or public-domain dog bark: the dog clip is CC BY-SA 3.0 (scratch folder only, not in the repo).
- Commons search returned paintings and aircraft ("Seagull", "Sparrow") for animal names; the photo script needed filters and
  better (scientific) names. Commons also rate-limits fast queries (empty answers); the scripts wait between calls.
- `soundfile` cannot read the Ogg Opus whistle; ffmpeg (from the repo venv's `imageio_ffmpeg`, used read-only) converted it.
- The first photo set's "bird" search gave warplanes: discarded before measuring (not used).
- The human clip's reference words are from memory of the LibriVox notice; there is no transcript file.
- A stray bare `python3` was typed once in a shell pipeline (a mistake against the rule); it produced no output and no installer appeared.
