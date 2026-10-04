# Project ideas for learners (0.1 feature set)

**Status:** ideas only, captured 4 October 2026 from a conversation with the maintainer. Nothing here is planned
except where `sprints/` says so.

**Purpose:** ambitious projects for beginners, and some for intermediates, that give great results with release
0.1. Later they could become a "Projects" guide chapter, a "Projects" gallery area, and challenge cards.

**Marks:**
- ⭐ needs a feature planned for Sprint 14 but not built yet: onsets and tempo, chords, the tala sequencer, the raga table and raga analysis.
- Projects without ⭐ use only features that exist today.

## Music and sound

| # | Project | What the learner builds | Features | Level |
|---|---|---|---|---|
| 1 | **Built (S-117)** Raga explorer ⭐ | Pick a raga; hear its aroha and avaroha over a tanpura drone; swaras light up on a ladder; sing it back and see your pitch line against Sa and Pa | `melody(sa=…, tuning="just")`, `pluck`/`tone` drone, `microphone`, `pitch`, `frequency_to_note(sa=…)`, controls, raga table | Beginner+ |
| 2 | **Partly built (S-108 tuner; the hold-a-note challenge is not)** Tuner and practice coach | A tuner with a needle, plus a "hold this note for 3 seconds" challenge scored for steadiness | `microphone`, `pitch`, `frequency_to_note`, `level` | Beginner |
| 3 | **Built (S-114)** Ear-training game | The sketch plays a note or interval; the learner sings or clicks the answer; score, streak, and a progress chart saved as PDF | `note`, `melody`, `microphone`, `pitch`, buttons, PDF | Beginner+ |
| 4 | **Built (S-114)** Visual music box | Compose on a clickable time × pitch grid; it loops; export the tune as WAV and the grid as a poster PDF | `note`/`pluck`, `sequence`, `mix`, `save("x.wav")`, mouse, PDF | Beginner |
| 5 | Sound portrait | Record 5 s of your voice; draw its wave, a spectrum ribbon and its pitch line as a print-ready artwork | `capture`, `samples`, `spectrum`, `pitch`, gradients, layered PDF/SVG | Intermediate |
| 6 | Music visualiser | Load a song; bars, rings and particles react to loudness and spectrum; record it as MP4 or GIF | `load_sound`, `level`, `spectrum`, `noise`, blend modes, `save_movie`/`save_gif` | Beginner+ |
| 7 | Beat-reactive light show ⭐ | Shapes flash on beats and change colour with the chord | onsets and tempo, chords, blend, shadows | Intermediate |
| 8 | Tala practice partner ⭐ | Teentaal or rupak with bols on screen; the sam glows; tap along and see whether you were early or late | tala sequencer, `pluck`/`tone`, keyboard timing | Beginner+ |
| 9 | Generative raga improviser ⭐ | A melody wanders within a raga's rules, with meend glides; sliders for mood, tempo and range; save takes as WAV | `melody`/`create_sound`, raga table, controls, `save` | Intermediate |

## Design and print

| # | Project | What the learner builds | Features | Level |
|---|---|---|---|---|
| 10 | **Built (S-117)** Event poster series | A poster per event from a list; Hindi and English text, emoji, gradients, rounded panels; a multi-page layered PDF for print, and SVGs for editing | pages, `text_box`, `FormattedString`, fallback fonts, layers, PDF/SVG | Beginner+ |
| 11 | Zine or recipe book | A multi-page booklet with filtered and masked photos, text flowing from page to page, page numbers | `new_page`, `text_box` overflow, `load_image`, filters, `mask` | Intermediate |
| 12 | Typographic portrait | A photo redrawn from letters whose size follows brightness; a vector PDF for large prints | `load_image`, `get`/pixels, `text`, PDF | Beginner+ |
| 13 | Kinetic type | A word made of dots that scatter on mouse-over and return; saved as a GIF | `text_to_points`, `Vector`, `noise`, `save_gif` | Beginner+ |
| 14 | Logo and badge maker | Shapes combined with booleans, letters as paths, rounded corners; clean SVG output | booleans, `text_path`, `expand_stroke`, SVG import and export | Intermediate |

## Games and interactive

| # | Project | What the learner builds | Features | Level |
|---|---|---|---|---|
| 15 | Scratch-card reveal game | Prizes under a foil layer scratched off with the mouse; sounds when one is found | `layer`, `erase`, `pluck`/`tone`, mouse | Beginner |
| 16 | **Built (S-117)** Voice-controlled game | A bird flies higher the louder or higher you sing; obstacles; a score | `microphone`, `level`/`pitch`, collisions, sound effects | Beginner+ |
| 17 | Drawing app with layers | Brush, eraser, colour sliders, layer show and hide, undo; save as PNG and a layered PDF | `layer`, `erase`, controls, `create_graphics`, PDF layers | Intermediate |

## Generative art

| # | Project | What the learner builds | Features | Level |
|---|---|---|---|---|
| 18 | Flow-field print | Thousands of noise-guided lines with blend modes on a trails layer; a vector PDF for A3 | `noise`, `Vector`, `layer`, blend, PDF | Beginner+ |
| 19 | **Built (S-117)** Rangoli and mandala generator | Symmetric patterns from rotations and booleans in festival palettes; sliders for petals and rings; SVG for printing or laser cutting | transforms, booleans, `color_mode("hsb")`, controls, SVG | Beginner+ |
| 20 | Living painting | A photo slowly repainted by brush particles that sample its colours; the process recorded as MP4 | `load_image`, `get`, `noise`, layers, `save_movie` | Intermediate |

## Candidate capstones

- **1, Raga explorer:** unique to funground. It combines synthesis, sargam, the microphone and visualisation, and teaches music and maths together.
- **10, Event poster series:** real-world use. It makes print-ready, editable, bilingual material for a learner's own school or community.
- **16, Voice-controlled game:** instant delight. It is playable within minutes of being finished.

## How they could ship (not decided)

1. A **Projects guide chapter**: step-by-step builds of a few capstones in stages: make it work, make it yours, make it shine.
2. A **Projects gallery area**: the finished versions, which learners copy to a folder and adapt.
3. **Challenge cards**: short "can you add…?" extensions for classrooms.
