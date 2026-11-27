# Third-party licences

Where each piece of software, method, data set, font and idea comes from is in [CREDITS.md](CREDITS.md). This page is about licences.

funground itself is licensed under the **GNU Lesser General Public License, version 2.1 only**
(`LGPL-2.1-only`; no later version applies); see [LICENSE](LICENSE). The software it
builds on keeps its own licence, listed here. Where the two differ, each component's own licence
governs that component.

## Example code

The sketches in `examples/` and the code blocks in the User Guide and Quick Reference are **not**
under the LGPL: they are dedicated to the public domain under **CC0 1.0**
([examples/LICENSE](examples/LICENSE)), so learners can reuse them freely. They are original to
funground; see [docs/qa/Example_Provenance.md](docs/qa/Example_Provenance.md).

## Included in funground

These are part of the funground package itself.

| Component | Where | Licence | Notes |
|---|---|---|---|
| DejaVu Sans fonts (Regular, Bold, Oblique, Bold Oblique), version 2.37 | `funground/fonts/` | Bitstream Vera Fonts licence; DejaVu's own changes are in the public domain | Full text in `funground/fonts/DejaVu-LICENSE.txt`, shipped with the package. The fonts may not be sold on their own, and a modified font must be renamed. |
| Noto Emoji (static instance at weight 400 of the variable font, version 3.002), Noto Sans Symbols 2, Noto Sans Devanagari | `funground/fonts/` | SIL Open Font License 1.1 (© Google LLC; © The Noto Project Authors) | Fallback fonts for letters the current font does not have (contract T18). Full text and copyright lines in `funground/fonts/Noto-OFL.txt`, shipped with the package. None declares a Reserved Font Name. The fonts may not be sold on their own. |
| Sound names (521, in `_sound_names.py`) | `ml/funground_ml/` (the separate package funground-ml) | CC BY 4.0, from the AudioSet ontology by Google LLC | The `display_name` column of YAMNet's class map; the header of the file says where it came from. The model itself, YAMNet by Google LLC, is Apache-2.0 and is downloaded, not included. |
| Noise function | `funground/noise.py` | LGPL-2.1, from p5.js (© the p5.js contributors) | A Python translation of p5.js's `noise()`, `noiseSeed()` and `noiseDetail()`, so seeded values match p5 exactly. Source: <https://github.com/processing/p5.js> |
| sRGB colour profile (`sRGB.icc`, 588 bytes) | `funground/data/sRGB.icc` | No third-party copyright. Made by littleCMS (MIT licence), which writes "No copyright, use freely" into the profile | Every PDF is tagged with it, so its RGB colours are defined (contract D4). Generated once by `tools/make_srgb_profile.py` with Pillow's `ImageCms.createProfile("sRGB")` on a developer machine; funground does not run littleCMS when it saves. Not an ICC-registry or vendor profile, so no vendor licence applies. |
| Colour-name table | `funground/_colornames.py` | Derived from pygame-ce's colour table (LGPL-2.1), which lists the X11 colour names from `rgb.txt` (X11/MIT-style licence) | Names and RGB values only |
| DejaVu Sans Mono font, version 2.37 | `examples/gallery/text/fonts/` (repository only, not in the installed package) | Bitstream Vera Fonts licence, as above | Used by one gallery example to show `load_font`; its licence file sits beside it. |

## Installed alongside funground

pip installs these as separate packages. funground imports them and includes none of their code.
Their licences apply to them as installed.

| Package | Licence | Includes |
|---|---|---|
| [pygame-ce](https://pyga.me) | LGPL-2.1 | [SDL](https://www.libsdl.org) (zlib licence) and other libraries in its wheels, each under its own licence |
| [pycairo](https://github.com/pygobject/pycairo) | LGPL-2.1-only or MPL-1.1 | [Cairo](https://www.cairographics.org) (LGPL-2.1 or MPL-1.1) and its dependencies in the wheels |
| [fontTools](https://github.com/fonttools/fonttools) | MIT | — |
| [uharfbuzz](https://github.com/harfbuzz/uharfbuzz) | Apache-2.0 | [HarfBuzz](https://harfbuzz.github.io) (Old MIT licence) |
| [skia-pathops](https://github.com/fonttools/skia-pathops) | BSD-3-Clause | a cut-down build of [Skia](https://skia.org)'s path code (BSD-3-Clause) |
| [svgelements](https://github.com/meerk40t/svgelements) | MIT | — |
| [pypdf](https://github.com/py-pdf/pypdf) | BSD-3-Clause | — |
| [Pillow](https://pillow.readthedocs.io) (optional, `funground[extras]`) | MIT-CMU (formerly called HPND) | Used for some picture filters when it is installed; funground works without it |
| [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) (optional, `funground[video]`) | BSD-2-Clause; the ffmpeg program it bundles is a GPLv3 build, run as a separate program and never linked | — |

The licence versions shown are those declared by the releases funground is tested with
(pygame-ce 2.5.8, pycairo 1.29.1, fontTools 4.66, uharfbuzz 0.56). Always check the package you
actually install.

## Models downloaded by funground-ml

funground-ml, the separate models package, downloads these files the first time a sketch needs one. They come from the
Hugging Face Hub, each pinned to a commit and checked against its SHA-256 before it is kept (the table is in
`ml/funground_ml/_models.py`). No funground package includes them. Two of them are funground's own copies, so for those
funground is the one who passes them on.

| Model | Used by | Where it comes from | Licence | Credit and changes |
|---|---|---|---|---|
| MediaPipe BlazePose: the person finder and the 33 body points | `ml.pose` | `opencv/person_detection_mediapipe`, `opencv/pose_estimation_mediapipe` | Apache-2.0 | Google LLC's models, converted to ONNX by the OpenCV Zoo. |
| MediaPipe hands: the palm finder and the 21 hand points | `ml.hand` | `opencv/palm_detection_mediapipe`, `opencv/handpose_estimation_mediapipe` | Apache-2.0 | Google LLC's models, converted to ONNX by the OpenCV Zoo. |
| MediaPipe selfie segmentation (general, 256 x 256) | `ml.person` | `onnx-community/mediapipe_selfie_segmentation` | Apache-2.0 | Google LLC's model, converted to ONNX by the `onnx-community` organisation. |
| Whisper tiny.en, quantized to 8 bits: encoder, decoder and `vocab.json` | `ml.words` | `onnx-community/whisper-tiny.en` | MIT, and Apache-2.0 | OpenAI's model. OpenAI's repository releases the code and weights under MIT (text below); its Hugging Face cards say Apache-2.0. Both allow this use, so both are kept. Converted and quantized by `onnx-community`. |
| YAMNet, the sound classifier | `ml.sound` | `funground-hq/yamnet-onnx`, funground's unchanged copy of `audiomagic/yamnet-onnx` | Apache-2.0 | Google LLC's model, converted to ONNX by audiomagic. |
| MobileNetV4-small, giving a vector of 1,280 numbers (the default picture model) | `ml.teach`, `ml.guess` | `funground-hq/mobilenetv4-small-vector-onnx` | Apache-2.0 | Google's architecture (Qin et al., 2024) with Ross Wightman's timm weights, trained on ImageNet-1k. **Changed by funground:** the classifier is cut off; the script that does it is in that repository. |
| DINOv2-small, quantized to 8 bits | `ml.teach`, `ml.guess` (`model="dinov2"`) | `onnx-community/dinov2-small` | Apache-2.0 | Meta AI's model, converted and quantized by `onnx-community`. |

The Apache-2.0 text is at <https://www.apache.org/licenses/LICENSE-2.0>.

**What the makers say the models are for.** The MediaPipe model cards put "any form of surveillance or identity
recognition" out of scope, and say the models work best for one person, near the camera. OpenAI's card asks people not
to transcribe recordings of others taken without their consent, and warns that Whisper can write words that were never
said. funground's model features are for making things with your own body, hands, voice and pictures, not for watching
or identifying people.

Whisper's MIT licence, from <https://github.com/openai/whisper>:

```text
MIT License

Copyright (c) 2022 OpenAI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Installed alongside funground-ml

| Package | Licence | Includes |
|---|---|---|
| [onnxruntime](https://onnxruntime.ai) | MIT (© Microsoft Corporation) | other libraries in its wheels, each under its own licence, listed in its ThirdPartyNotices file |
| [NumPy](https://numpy.org) | BSD-3-Clause | parts under 0BSD, MIT, Zlib and CC0-1.0, as its package declares |
| [Pillow](https://pillow.readthedocs.io) | MIT-CMU | — |

Checked with onnxruntime 1.32.0, NumPy 2.5.4 and Pillow 12.3.0.

## Play, in the browser

Play, the editor on funground's website, runs funground in the browser with Pyodide and runs the models with ONNX
Runtime Web. Those, and the editor's own libraries and fonts, are listed on the website's
[third-party notices](https://funground-hq.github.io/notices/) page.

## Inspirations, no code taken

funground borrows ideas and function names from these projects but none of their code, apart from
the noise function above:

- [Processing](https://processing.org): core library LGPL-2.1.
- [p5.js](https://p5js.org): LGPL-2.1.
- [DrawBot](https://www.drawbot.com): BSD-style licence.
- [The Nature of Code](https://natureofcode.com/) (Daniel Shiffman): a book whose ideas on motion and forces the examples
  resemble; its example collections were used only as a comparison set for the originality check.

The methods, books and papers behind the sound and the raga data are credited in [CREDITS.md](CREDITS.md).
