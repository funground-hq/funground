# S-174 audit: option words, proposed constants, conflicts

Read-only audit, 14 Oct 2026, branch sprint-25. Paths are under C:\Projects\playground\funground\ unless stated.

General facts
- No `Literal[` exists anywhere in funground/ today. Every option parameter is annotated plain `str` (api.py signatures).
- Module-level `f.name()` functions are thin wrappers in api.py that call the active `Sketch` method (sketch.py). A
  `Graphics`/`Picture` (picture.py:144) is not a separate API: `Picture.__getattr__` (picture.py:246) hands every drawing
  method to its own Sketch, so `g.rect_mode(...)`, `g.blend_mode(...)` etc. take exactly the same words. Only
  `Picture.save` (picture.py:481) and `Picture.image` (picture.py:450) are real Picture methods.
- All validation is exact-match and case-sensitive, with no aliases (no "centre", no "grey" for the filter, no
  "top_left"), except the four places marked CI below.
- Validation is `x not in <table>` followed by a ValueError listing the words.

## 1. Every parameter that takes an option word

Kind: F = module-level `f.` function (wrapper line in api.py, check in the file given); M = method on an object.
"CI" = case-insensitive.

| Function | Parameter | Words | Validated at | Case / aliases | Kind |
|---|---|---|---|---|---|
| rect_mode (api.py:966) | mode | corner, corners, center, radius | sketch.py:1733 (RECT_MODES), check in `_set_mode` sketch.py:1750 | exact | F (also g.rect_mode) |
| ellipse_mode (api.py:986) | mode | center, radius, corner, corners | sketch.py:1734, 1750 | exact | F |
| image_mode (api.py:1006) | mode | corner, corners, center | sketch.py:1735, 1750 | exact | F |
| arc (api.py:1133) | mode (default "open") | open, chord, pie | sketch.py:1840 table, check 1849-1850 | exact | F |
| color_mode (api.py:1573) | mode | rgb, hsb, hsl | color.py:441 (COLOR_MODES), check sketch.py:1289-1290 | exact | F |
| blend_mode (api.py:1598) | mode | normal, multiply, screen, overlay, darken, lighten, add, difference, exclusion, dodge, burn, hard_light, soft_light, hue, saturation, color, luminosity (17) | sketch.py:2167 (BLEND_MODES), check 2200-2201 | exact | F |
| text_align (api.py:1279) | horizontal | left, center, right, justify | sketch.py:1507 (TEXT_ALIGNS), check 1523-1524 | exact | F |
| text_align | vertical (optional) | top, center, baseline, bottom | sketch.py:1514 (TEXT_VALIGNS), check 1525-1526 | exact | F |
| text_style (api.py:1963) | style | normal, bold, italic, bold_italic | typography.py:38-44 (STYLE_FILES, TEXT_STYLES), check sketch.py:1463-1464 | exact | F |
| FormattedString.append | style (optional) | same four | check formatted.py:178-180 (TEXT_STYLES) | exact | M |
| stroke_cap (api.py:1776) | cap | round, square, butt | sketch.py:1339 (STROKE_CAPS), check 1353-1354 | exact | F |
| stroke_join (api.py:1793) | join | round, miter, bevel | sketch.py:1345 (STROKE_JOINS), check 1358-1359 | exact | F |
| PathBuilder.expand_stroke (paths.py:347) | cap, join (defaults "round") | as stroke_cap, stroke_join | pathops.py:128-129 (_CAPS, _JOINS), check pathops.py:153-156 | exact | M |
| cursor (api.py:787) | kind (default "arrow") | arrow, cross, hand, move, text, wait | platform/base.py:29 (CURSOR_KINDS), check sketch.py:650-652 | exact | F |
| filter / apply_filter (api.py:3551, 3572) | kind | threshold, gray, opaque, invert, blur, posterize, erode, dilate | imaging.py:211 (FILTER_KINDS), check imaging.py:233 (called sketch.py:1023-1027) | exact | F |
| tone (api.py:2842) | wave (default "sine") | sine, square, saw, triangle, soft, noise | synth.py:20 (WAVES), `_check_wave` synth.py:125-127, called synth.py:301 | exact | F |
| note (api.py:2873) | wave (default "sine") | same six | same path | exact | F |
| melody (api.py:2932) | wave (default "soft") | same six | synth.py:390 | exact | F |
| melody | tuning (default "equal") | equal, just | synth.py:392 (inline tuple, no table) | exact | F |
| Mark.place (marks.py:413) | anchor (default "origin") | origin, center, top-left, top, top-right, left, right, bottom-left, bottom, bottom-right | marks.py:40, 53 (ANCHOR_MEANINGS, ANCHORS), check marks.py:455-456 | exact | M |
| Mark.place | style (default "own") | own, current | marks.py:457-458 (inline tuple) | exact | M |
| save (api.py:721) | text (default "live") | live, shapes | export/__init__.py:41 (TEXT_MODES), check 44-48; called sketch.py:1044 | exact | F |
| Picture.save (picture.py:481) | text | live, shapes | same check | exact | M |
| size (api.py:333) / new_page (api.py:399) / page_size (api.py:436) | width (when a str), name | A3, A4, A5, B5, Letter, Legal, Tabloid, Square; optional suffix "Landscape" ("A4Landscape") | pages.py:7-16 (PAGE_SIZES), lookup pages.py:23-33; callers sketch.py:317-325, 397-412 | CI (pages.py:18, 26: lower-cased, stripped); landscape also by `landscape=True` | F |
| key_down (api.py:3594) | key (str or int) | left, right, up, down, space, enter, escape, or any one character | platform/base.py:20-27 (KEY_NAMES), check sketch.py:2303-2307 | CI (sketch.py:2305 lower-cases) | F |
| live value `mouse_button` (api.py:93) | a value read, not a parameter | left, center, right | platform/base.py:49 (MOUSE_BUTTONS); set sketch.py:2320-2321 | exact | read-only value learners compare with |
| live value `key` (api.py:106) | a value read | single characters, plus the KEY_NAMES words for named keys | pygame_platform.py:349 | exact | read-only value |
| save / save_gif / save_movie / save_frames (api.py:721 ...) | the file extension in `path` | png, pdf, svg (FORMATS export/__init__.py:40, `format_of` 93-97); gif, mp4 (MOTION_FORMATS export/motion.py:19; sketch.py:1056-1058) | as left | CI (`.lower()` sketch.py:1049, 1058) | F; not a parameter, part of a file name |
| live_value (api.py:203) | name | width, height, mouse_x, ... (15 names, LIVE_NAMES api.py:35) | api.py:35 | exact | F (variable names, not option words) |
| raga (api.py:3086), tala / tala_info (api.py:3145) | name | data names: 13 ragas (Yaman, Bhupali ...), 6 talas (Teentaal, Ektaal, Jhaptaal, Rupak, Dadra, Keherwa) | hindustani.py:155, 163 (find_raga, find_tala) | table lookup | F (an open data table, not a fixed option set) |

Not option words, checked: begin_shape()/end_shape(close=bool) (no kind argument; shapes.py/ sketch.py:2059, 2085);
gradients (linear_gradient, radial_gradient take numbers and colours only, paint.py:75, 80); Sound, Microphone, slider,
button, checkbox methods (controls.py, sound.py, microphone_input.py: no string option parameters, checked by
signature introspection); `text_features(**features: bool)` and `font_variations(**axes)` (keyword names are OpenType
tags, an open set); `Grid.show(color=)` (a colour); internal tuples sketch.py:1575, 1684, 1775 and
platform/base.py:48 (EVENT_KINDS) are not learner-facing.

Items with meanings tables today (S-179 / D-092, tools/make_api_reference.py:116-132 WORD_MEANINGS): blend_mode,
stroke_cap, stroke_join, expand_stroke, text_align (both), text_style, FormattedString.append, filter, apply_filter,
cursor, key_down, tone, note, melody (wave), Mark.place (anchor). Sets with NO table: rect_mode, ellipse_mode,
image_mode, arc mode, color_mode, melody tuning, Mark.place style, save text, page sizes, mouse_button. The constants
story could add tables for these.

## 2. The proposed flat constant list

Rule: constant = word upper-cased, `-` and spaces to `_`; value = the word exactly as accepted today (so strings keep
working and existing code is unchanged). 83 distinct constants. "Shared" means the same word used in several places, which
is exactly p5's flat model.

| Constant | Value | Used by (function.parameter) |
|---|---|---|
| CORNER | "corner" | rect_mode.mode, ellipse_mode.mode, image_mode.mode |
| CORNERS | "corners" | rect_mode.mode, ellipse_mode.mode, image_mode.mode |
| CENTER | "center" | rect_mode.mode, ellipse_mode.mode, image_mode.mode, text_align.horizontal, text_align.vertical, Mark.place.anchor, mouse_button (read) |
| RADIUS | "radius" | rect_mode.mode, ellipse_mode.mode |
| OPEN | "open" | arc.mode |
| CHORD | "chord" | arc.mode |
| PIE | "pie" | arc.mode |
| RGB | "rgb" | color_mode.mode |
| HSB | "hsb" | color_mode.mode |
| HSL | "hsl" | color_mode.mode |
| LEFT | "left" | text_align.horizontal, Mark.place.anchor, key_down.key, mouse_button (read) |
| RIGHT | "right" | text_align.horizontal, Mark.place.anchor, key_down.key, mouse_button (read) |
| JUSTIFY | "justify" | text_align.horizontal |
| TOP | "top" | text_align.vertical, Mark.place.anchor |
| BASELINE | "baseline" | text_align.vertical |
| BOTTOM | "bottom" | text_align.vertical, Mark.place.anchor |
| NORMAL | "normal" | text_style.style, FormattedString.append.style, blend_mode.mode |
| BOLD | "bold" | text_style.style, FormattedString.append.style |
| ITALIC | "italic" | text_style.style, FormattedString.append.style |
| BOLD_ITALIC | "bold_italic" | text_style.style, FormattedString.append.style |
| ROUND | "round" | stroke_cap.cap, stroke_join.join, expand_stroke.cap, expand_stroke.join |
| SQUARE | "square" | stroke_cap.cap, expand_stroke.cap, tone/note/melody.wave, size/new_page/page_size (page "Square", CI) |
| BUTT | "butt" | stroke_cap.cap, expand_stroke.cap |
| MITER | "miter" | stroke_join.join, expand_stroke.join |
| BEVEL | "bevel" | stroke_join.join, expand_stroke.join |
| ARROW | "arrow" | cursor.kind |
| CROSS | "cross" | cursor.kind |
| HAND | "hand" | cursor.kind |
| MOVE | "move" | cursor.kind |
| TEXT | "text" | cursor.kind |
| WAIT | "wait" | cursor.kind |
| MULTIPLY | "multiply" | blend_mode.mode |
| SCREEN | "screen" | blend_mode.mode |
| OVERLAY | "overlay" | blend_mode.mode |
| DARKEN | "darken" | blend_mode.mode |
| LIGHTEN | "lighten" | blend_mode.mode |
| ADD | "add" | blend_mode.mode |
| DIFFERENCE | "difference" | blend_mode.mode |
| EXCLUSION | "exclusion" | blend_mode.mode |
| DODGE | "dodge" | blend_mode.mode |
| BURN | "burn" | blend_mode.mode |
| HARD_LIGHT | "hard_light" | blend_mode.mode |
| SOFT_LIGHT | "soft_light" | blend_mode.mode |
| HUE | "hue" | blend_mode.mode |
| SATURATION | "saturation" | blend_mode.mode |
| COLOR | "color" | blend_mode.mode |
| LUMINOSITY | "luminosity" | blend_mode.mode |
| THRESHOLD | "threshold" | filter.kind, apply_filter.kind |
| GRAY | "gray" | filter.kind, apply_filter.kind |
| OPAQUE | "opaque" | filter.kind, apply_filter.kind |
| INVERT | "invert" | filter.kind, apply_filter.kind |
| BLUR | "blur" | filter.kind, apply_filter.kind |
| POSTERIZE | "posterize" | filter.kind, apply_filter.kind |
| ERODE | "erode" | filter.kind, apply_filter.kind |
| DILATE | "dilate" | filter.kind, apply_filter.kind |
| SINE | "sine" | tone/note/melody.wave |
| SAW | "saw" | tone/note/melody.wave |
| TRIANGLE | "triangle" | tone/note/melody.wave |
| SOFT | "soft" | tone/note/melody.wave |
| NOISE | "noise" | tone/note/melody.wave |
| EQUAL | "equal" | melody.tuning |
| JUST | "just" | melody.tuning |
| ORIGIN | "origin" | Mark.place.anchor |
| TOP_LEFT | "top-left" | Mark.place.anchor |
| TOP_RIGHT | "top-right" | Mark.place.anchor |
| BOTTOM_LEFT | "bottom-left" | Mark.place.anchor |
| BOTTOM_RIGHT | "bottom-right" | Mark.place.anchor |
| OWN | "own" | Mark.place.style |
| CURRENT | "current" | Mark.place.style |
| LIVE | "live" | save.text, Picture.save.text |
| SHAPES | "shapes" | save.text, Picture.save.text |
| UP | "up" | key_down.key |
| DOWN | "down" | key_down.key |
| SPACE | "space" | key_down.key |
| ENTER | "enter" | key_down.key |
| ESCAPE | "escape" | key_down.key |
| A3 | "A3" | size/new_page/page_size |
| A4 | "A4" | same |
| A5 | "A5" | same |
| B5 | "B5" | same |
| LETTER | "Letter" | same |
| LEGAL | "Legal" | same |
| TABLOID | "Tabloid" | same |

(That is 83 rows counting SQUARE once. Without the 7 page names it is 76. The page names are optional: size("A4")
reads as well as size(A4), and `Square` is the only one that overlaps another word.)

Words that are not given a constant: file extensions (png, pdf, svg, gif, mp4, part of a file name), raga and tala names
(data, an open table), live-value names, "Landscape" (a suffix or `landscape=True`, not a word on its own; an
`A4_LANDSCAPE` family would add 7 more and is not recommended), key names beyond the seven (a single character is the
rest).

Words shared across functions with DIFFERENT meaning (sharing the string is fine, but the reference should say so):
- left / right: text starts at x (text_align), a mark's anchor point, an arrow key, a mouse button.
- center: x is the middle (text_align), the mark's bounds middle (anchor), the box is read from its middle (rect/ellipse/image mode), the middle mouse button; and vertical text_align "center" is halfway between top and bottom.
- top / bottom: y is the top/bottom of text (text_align.vertical) versus the mid-top / mid-bottom point of a mark (anchor).
- corner / corners / radius / center: same words in rect_mode, ellipse_mode and image_mode, but the defaults and which words exist differ per function (image_mode has no "radius"; arc follows ellipse_mode). The list of valid words is therefore per function, not per constant: `image_mode(RADIUS)` is accepted by the constant name and then refused at run time. `Literal` types per parameter fix this for editors.
- normal: no change in text_style, "paint over" in blend_mode.
- round: line ends versus corners. square: a cap, a wave, a page size and a function. soft: a wave only. color: a blend mode, not the colour type.
- text: the I-beam cursor, versus the text() function.
- gray: a filter, versus the colour "gray".

## 3. Conflicts to bring to the maintainer

### 3.1 Constant names equal (case-insensitively) to an existing public name (checked against `funground._PUBLIC_NAMES`, 205 names)

Seven, all functions in __init__.py:

| Constant | Existing name | Use | Recommendation |
|---|---|---|---|
| SQUARE | square() | stroke cap, wave, page | Keep. Python is case-sensitive: `f.SQUARE` and `f.square` coexist (as p5 has `SQUARE` and `square()`). |
| TRIANGLE | triangle() | wave | Keep, same reason (p5 also has TRIANGLES and triangle()). |
| TEXT | text() | cursor | Keep (p5 has TEXT and text()). |
| NOISE | noise() | wave | Keep. |
| COLOR | color() | blend mode | Keep, or name it `COLOR_BLEND`; "color" is a standard CSS/Photoshop blend name, so keep. |
| HSB | hsb() | color_mode | Keep (p5 has HSB, and hsb is its own function here). |
| HSL | hsl() | color_mode | Keep. |

Recommendation: accept all seven. The risk is not Python (names differ by case) but (a) editors with case-insensitive
completion: `completions.json` and the Play editor sort and filter names; make the completion matching case-sensitive
or list constants in their own group; (b) learners reading `f.TEXT` vs `f.text` as the same; (c) tools/make_api_reference.py
(`all_names` grouping, line 438-444) and the anchors generated from names must not lower-case names into one anchor
(`#text` vs `#TEXT`); check Markdown heading slugs. If the maintainer prefers zero overlap, the alternative is suffixes
(`TEXT_CURSOR`, `NOISE_WAVE`) which break the one-word-one-name rule; not recommended.

Also: no existing public name is a lower-case option word other than the seven above (also checked: key, cursor,
filter, mouse_button are public names but no constant is named after them; the live value `key` and function `cursor`
are untouched).

### 3.2 Collisions with capital names already present

- `dir(funground)` capitals: STAR_LEAVES_OUT, STAR_NAMES_FOR, TYPE_CHECKING, `_PUBLIC_NAMES`, `_RENAMED` only. No clash.
- Capitals in funground modules matching a proposed name: none found (scripted scan of every loaded funground.* module;
  color.py has WHITE and BLACK at lines 435-436, which are not in the list and not public; they would collide only if a
  colour-name constant were made flat, see 3.5).
- Built-in or keyword clashes after upper-casing: none exist as such (Python names are case-sensitive); `ROUND` and
  `OPEN` look like the built-ins `round` and `open` only in lower case. tests/test_global_style.py:29-32 requires
  `__all__` to be free of built-in or standard-library names; upper-case names pass.
- A name used as an option word and also as a colour: GRAY (filter) versus `colors.GRAY` (colour). Different
  namespaces, so no clash (another reason colours must stay under `f.colors`).

### 3.3 Star import (`from funground import *`, D-088)

Two separate issues.

(a) Learner variables. Constants in `__all__` land in the learner's globals. Common learner constant names that
would be overwritten or overwrite funground's meaning: RADIUS (very common), SPACE, TOP, BOTTOM, LEFT, RIGHT, UP,
DOWN, CENTER, COLOR, SCREEN, ADD, MOVE, WAIT, CROSS, HAND, OPEN, ROUND, NORMAL, BOLD, SOFT, SAW, HUE, BLUR, GRAY,
LIVE, ENTER, ESCAPE, EQUAL, JUST, OWN, CURRENT, ORIGIN, LETTER, LEGAL, A3 ... A5, B5, TEXT, NOISE. Because the star
import comes first, the learner's own assignment simply wins in their file (`RADIUS = 40` works); the only loss is
that the funground meaning of that name is unavailable there. Unlike a function (`size = 40` hides `size()` and raises
the confusing "not callable"), a shadowed constant does not fail strangely: `rect_mode(RADIUS)` with `RADIUS = 40`
passes 40 and raises the normal "takes one of ..." ValueError. `global_style.clash_note` (global_style.py:70-86) only
considers callables, so it stays silent.

Recommendation: include the constants in the star import (p5-style sketches need `rect_mode(CENTER)` to read
well; leaving them out defeats the point for the style D-088 supports). Mention in the guide that a variable with a
constant's name hides it. Do not use a different import.

(b) Machinery that assumes every public name is a function. `global_style._funground_functions`
(global_style.py:22-32) builds `frozenset(id(getattr(funground, name)) for name in _PUBLIC_NAMES if name not in
LIVE_NAMES)` and `uses_global_style` (global_style.py:35-41) says "global style" if ANY global's id is in that set. A
constant's value is a short string; CPython interns/shares equal string literals, so a plain `import funground as f`
sketch holding `align = "center"` could be mis-detected as global style, which would start the live-value refreshing
(global_style.py:44-50, which overwrites a variable named `width` in an `import funground as f` sketch: the exact bug the
module comment says it prevents). The constants must be excluded from that set (build it from callables, or exclude a
new CONSTANT_NAMES set). Also: tests/test_api_contract.py:289 pins `_PUBLIC_NAMES` to V05_FUNCTIONS | ADDED_FUNCTIONS |
LIVE_VALUES; tests/test_typing.py:57 loops `_PUBLIC_NAMES` (check if it assumes callables/annotations);
tests/test_completions.py:41 pins completions names to `_PUBLIC_NAMES`; tools/make_api_reference.py:65 and 438-444
require every public name to be in exactly one group, and the API.md/llms.txt generators need a "Constants" group.
Decide whether constants go inside `_PUBLIC_NAMES` (then all of these change) or a parallel `_CONSTANT_NAMES`
(then the star import needs them added to `__all__` by hand, and test_typing.py:36 requires `__all__` to be a literal list).

### 3.4 Names that are not valid identifiers or start with a digit

- Anchors "top-left", "top-right", "bottom-left", "bottom-right" contain hyphens: TOP_LEFT etc. (value keeps the hyphen).
  Recommendation: keep the hyphenated words (already documented; the value is invisible to learners who use
  constants) and document the constant form. Alternatively also accept "top_left" as an alias (new behaviour, a
  semantic-contract change, not needed).
- "A3", "A4", "A5", "B5" start with a letter, so are valid identifiers (A4 does not start with a digit).
  "Letter" and "Legal" values are capitalised: LETTER = "Letter" (pages are CI so either value works; recommend the
  capitalised canonical key from PAGE_SIZES).
- "bold_italic", "hard_light", "soft_light": underscores, fine.
- No option word starts with a digit.

### 3.5 `f.colors`

- Source: funground/_colornames.py, `NAMED_COLORS` (line 13), 665 names, all lower case, all valid identifiers once
  upper-cased, none starts with a digit (checked by script). 514 contain a digit (antiquewhite1 to 4, gray0 to gray100 and
  grey0 to grey100, and the numbered X11 families), 151 do not.
- Attribute form: `name.upper()`: TOMATO, ANTIQUEWHITE1, GRAY50, LIGHTGOLDENRODYELLOW. No underscores inserted (the
  names are already one word, and inserting would not be derivable from the table). Gap: long names are hard to read
  (LIGHTGOLDENRODYELLOW); that is the X11 spelling the strings already use.
- Value: recommend the name string ("tomato", "antiquewhite1"), not hex and not a Color. Reasons: every place that
  accepts a colour accepts a name (`_parse_color_string`, color.py:343-350, strips, lower-cases, removes spaces, so
  the lookup is the same code); `print(f.colors.TOMATO)` shows a word; the value is what the learner would have typed,
  so strings and constants are interchangeable (D-090 "strings still accepted"); no second source of truth for the
  RGBA (the same table, so the CSS "grey" and X11 meanings cannot drift). Hex would be opaque and a Color object
  would not be a str (breaks `f.colors.TOMATO == "tomato"` and Literal typing). Cost: a typo in a name string is only caught by a
  type checker or at the call.
- Typing: a class (or module with `__getattr__` plus a stub) with 665 `Final` / `Literal` attributes so editors list
  them; `completions.json` already lists colours (D-102); generate the class from `NAMED_COLORS` with a test that the
  two agree.
- Duplicates: 150 groups share an RGBA value. Seven are real synonyms with no digit: gray/grey, darkgray/darkgrey,
  lightgray/lightgrey, slategray/slategrey, darkslategray/darkslategrey, lightslategray/lightslategrey,
  navy/navyblue. Others are the numbered variants (gray0 and grey0 etc.: 101 pairs for gray/grey, 0..100, plus
  numbered duplicates of base colours, e.g. antiquewhite1 differs from antiquewhite, but some numbered X11 colours equal a base
  colour). Recommendation: keep all 665 (every name already accepted must keep working; GRAY and GREY both). Do not
  add British "colours": the API uses American spelling (AGENTS.md); but `f.colours` as an alias is cheap and
  friendly; maintainer's choice, not recommended (two names to one thing).
- Is `colors` a free public name? Yes. `colors` is not in `_PUBLIC_NAMES` (checked), there is no
  `funground/colors.py` (directory listing), and `colors` is not a public function so the naming trap in AGENTS.md
  (a submodule must not share a public function's name) does not bite. A submodule `funground/colors.py` would be safe only if `__init__` then rebinds `colors` to the class (as `funground/color.py` and the function `color` already coexist: `f.color` is the function today). Recommend a class `colors` defined in color.py or a new `_colorset.py` and exported, not a submodule. Name
  risk: `colors` is also (a) a parameter name (`linear_gradient(..., colors, stops)`, api.py:1524, 1549; harmless, local)
  and (b) an extremely common learner variable (`colors = ["red", "blue"]`). In the star style, `colors` would be put in
  the learner's globals and silently hidden by their list; `colors.TOMATO` would then fail with AttributeError on a list
  ("'list' object has no attribute 'TOMATO'"). Recommend adding a clash sentence for this case (the existing
  `explain_clash` handles TypeError "not callable" and NameError only, global_style.py:94-101; AttributeError
  would need adding), or accept it; the `import funground as f` style is unaffected.
- Collisions between colour attributes and option constants do not matter if colours stay under `f.colors`
  (GRAY is the only overlap). Flat colours (`f.TOMATO`, 665 new names, `WHITE`/`BLACK` already in color.py) are
  not proposed and would also swamp the star import.

## 4. Count of new public names

- 83 option constants (76 without the 7 page-size names), plus 1 for `colors` = 84 new top-level public names
  (77 without page sizes).
- 665 attributes inside `f.colors` (not top-level names; 665 completions entries, which completions.json could list under `colors.`).
- Existing public names: 205 (`_PUBLIC_NAMES`), 201 in `__all__`, 4 left out of the star (exit, filter, random, set).
  After the change: 289 public names (285 in `__all__`), or 282 without page names.
- Docs impact: a "Constants" group in tools/make_api_reference.py (line 65, 438-444), a table row for each new word
  family in the Quick Reference, completions.json entries, tests/test_api_contract.py:289, and a meanings
  table for the ten sets that have none today (rect/ellipse/image mode, arc, color_mode, tuning, place style, save text,
  page sizes, mouse_button).
- `Literal[...]` types: about 26 parameters / 24 functions (list in section 1) change annotation. Sets that already
  have a table can share `Literal[tuple(table)]`-style declarations only if declared literally in code (type checkers
  cannot read dict keys): the `Literal` alias must be written out by hand and a test must check it equals the table
  keys, otherwise two lists drift. That test is a good S-174 acceptance check.
