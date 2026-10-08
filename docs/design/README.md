# Design notes and decisions

Everything in `docs/design/`, in one list. Read the note for the code you are about to touch. For how
the code is built now, start with [Architecture.md](../developer/Architecture.md). If a note and the
source disagree, the source and the tests win. Notes record why. The ADRs and the decision log are never
rewritten after acceptance.

## The pinned behaviour and the decisions

| File | What it covers | Read it when |
|---|---|---|
| [Semantic_Contract.md](Semantic_Contract.md) | The pinned meaning of every public behaviour, one row each (C, S, F, T, P, R, A, M, U, D families). | Before you change or add any behaviour. |
| [Decision_Log.md](Decision_Log.md) | Every decision (D-nnn): date, options, outcome, who decided. | You want to know why something is the way it is, or you are about to make a decision. |

## ADRs (long-lived decisions)

| File | What it covers | Read it when |
|---|---|---|
| [ADR-001-renderer-topology.md](ADR-001-renderer-topology.md) | funground owns the meaning and the IR; pygame-ce is the window; renderers consume the IR. | You want to change who draws what, or add a renderer. |
| [ADR-002-renderer-selection-reopened.md](ADR-002-renderer-selection-reopened.md) | Cairo is the reference renderer; an engine is picked by measurement. | You are tempted to swap the rasteriser. |
| [ADR-003-out-of-scope.md](ADR-003-out-of-scope.md) | What funground deliberately does not do. | A request sounds like a new feature and you want to know if it is in scope. |
| [ADR-004-image-provider.md](ADR-004-image-provider.md) | pygame-ce reads image files; Pillow is optional. | You touch `imaging.py` or add an image format. |
| [ADR-005-path-operations.md](ADR-005-path-operations.md) | Path booleans and stroke expansion use skia-pathops. | You touch `pathops.py` or path booleans. |
| [ADR-006-simple-tones.md](ADR-006-simple-tones.md) | Simple tones and notes, without a real-time synthesis engine. | You touch `synth.py` or want a new kind of sound. |

## Design notes, by subsystem

| File | What it covers | Read it when |
|---|---|---|
| [Text_Subsystem_Note.md](Text_Subsystem_Note.md) | Text drawn as glyph outlines, shaping, the bundled font. | You touch `typography.py` or how text is drawn. |
| [Typography_Note.md](Typography_Note.md) | Fonts, styles, tracking, OpenType features, variations, mixed text. | You change text settings or `FormattedString`. |
| [PDF_Text_Note.md](PDF_Text_Note.md) | Real, searchable text in PDFs, by marker groups and pypdf. | You touch `export/pdf_text.py` or a PDF text bug. |
| [Text_In_Files_Note.md](Text_In_Files_Note.md) | Live, editable `<text>` in SVG files, with font names and embedded subsets. | You touch `export/svg_text.py` or hand files to Illustrator or Inkscape. |
| [Layers_Note.md](Layers_Note.md) | `f.layer()` as pictures on screen and as real layers in PDF and SVG. | You touch layers, `active_sketch()` or `export/layers.py`. |
| [Compositing_Note.md](Compositing_Note.md) | Colour modes, gradients, blend modes, opacity and shadows. | You touch colour, paint or compositing. |
| [Paths_Note.md](Paths_Note.md) | Paths, drawing modes, booleans, rounded corners. | You touch `geometry.py`, `paths.py` or `pathops.py`. |
| [Pictures_and_Images_Note.md](Pictures_and_Images_Note.md) | Pictures, images and pixels, history and flushing. | You touch `picture.py` or `imaging.py`. |
| [SVG_Import_Note.md](SVG_Import_Note.md) | SVG files as vector pictures. | You touch `svg.py` or `f.load_svg()`. |
| [Scripts_and_Pages_Note.md](Scripts_and_Pages_Note.md) | Script mode, pages and multi-page documents. | You touch `new_page`, `show()` or the script canvas. |
| [Sound_Making_Note.md](Sound_Making_Note.md) | Making sound from numbers, sound quality, the microphone, drawing sound. | You touch `synth.py`, `sound.py`, `microphone_input.py` or `sound_views.py`. |
| [Music_Analysis_Note.md](Music_Analysis_Note.md) | Onsets, tempo, beats, chroma, chords and key. | You touch `analysis.py` or the rhythm and harmony methods. |
| [Ragas_Note.md](Ragas_Note.md) | Ragas and talas: sources, methods and limits. | You touch `hindustani.py` or `data/ragas.json`, or add a raga. |
| [Browser_Mode_Note.md](Browser_Mode_Note.md) | Research: funground in a web browser. Directional, not in 0.1. | Someone asks for a browser version. |
| [Web_Target_Options.md](Web_Target_Options.md) | Options study for 0.2 on the web: inventory, five architectures, spikes, open decisions. Nothing decided. | You plan web work for 0.2. |

## Research and history

| File | What it covers | Read it when |
|---|---|---|
| [Music_Research_Note.md](Music_Research_Note.md) | The options for music (making, playing, listening) that were weighed before D-055 to D-057. | You want the reasons and the outside libraries that were not chosen. |
| [Playground_Technology_Architecture_v2.md](Playground_Technology_Architecture_v2.md) | The Sprint 2 architecture record. History only. | You want the reasons behind the first design. Current code is in [Architecture.md](../developer/Architecture.md). |
| [Playground_Technology_Architecture.docx](Playground_Technology_Architecture.docx) | The first (v1) architecture document. History only. | Almost never. It is the starting point that the review and v2 replaced. |
| [Playground_Architecture_Review.md](Playground_Architecture_Review.md) | A critique of v1 and the revised plan that led to v2. History only. | You want to know why v1 changed. |
