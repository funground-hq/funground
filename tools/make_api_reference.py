"""Generate docs/reference/API.md from the docstrings and the data tables in funground (D-066).

Run:    .venv/Scripts/python tools/make_api_reference.py
Check:  .venv/Scripts/python tools/make_api_reference.py --check     (exit 1 if a page is out of date)

It also writes the pages for AI assistants (S-129, llmstxt.org): llms.txt (the rules in
docs/reference/llms_rules.md, then links) and llms-full.txt (the rules, then this whole reference as
plain Markdown), each at the repository root and inside the package.

The output is fully deterministic: fixed order, no dates.

Docstring format (parsed by parse_doc below; tests/test_api_docs.py holds the rules):
    Summary sentence.            blank line, prose
    Arguments:   x, y: text      (indented entries, continuation lines indented more)
    Returns:     text
    Raises:      ValueError: text
    Example:     code
    See also: a, b
"""
from __future__ import annotations

import importlib
import ast
import inspect
import json
import re
import sys
import textwrap
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import since  # noqa: E402  (which release a name arrives in, S-229)
import funground as f  # noqa: E402
from funground import _colornames, api as _api, pages, synth  # noqa: E402
from funground import analysis, marks, typography  # noqa: E402
from funground._namespaces import NAMESPACE_NAMES  # noqa: E402
_color = sys.modules["funground.color"]  # f.color (the function) hides the module as an attribute
from funground.export import FORMATS, TEXT_MODES  # noqa: E402
from funground.export.motion import MOTION_FORMATS  # noqa: E402
from funground.imaging import FILTER_KINDS  # noqa: E402
from funground.platform.base import CURSOR_KINDS, KEY_NAMES, MOUSE_BUTTONS  # noqa: E402
from funground.sketch import CALLBACK_NAMES, Sketch  # noqa: E402

OUT = ROOT / "docs" / "reference" / "API.md"
COMPLETIONS = ROOT / "funground" / "completions.json"
COLORS_CLASS = ROOT / "funground" / "_color_names_class.py"
CLASS_LIST = ROOT / "docs" / "reference" / "api_classes.txt"
RULES = ROOT / "docs" / "reference" / "llms_rules.md"
REPO_URL = "https://github.com/funground-hq/funground/blob/main/"
LLMS_SUMMARY = ("funground is a Python library for drawing, animation, typography, print and sound, made for "
                "learning. `import funground as f`.")
# llms.txt's links: (title, path in the repository, when to read it).
LLMS_LINKS = [
    ("API reference", "docs/reference/API.md", "every public name, with its arguments and an example"),
    ("Quick Reference", "docs/reference/Quick_Reference.md", "every function by topic, with pictures"),
    ("funground compared with p5 and DrawBot", "docs/reference/Compared_with_p5_and_DrawBot.md",
     "what each p5 or DrawBot name is called here"),
    ("User Guide", "docs/guide/README.md", "chapters from a first sketch to print, sound and projects"),
    ("When something goes wrong", "docs/guide/errors.md", "what each error message means"),
    ("Examples Gallery", "docs/gallery/README.md", "a small, tested sketch for every feature"),
]

SECTIONS = ("Arguments", "Returns", "Raises", "Example")

# Every name in funground._PUBLIC_NAMES must be in exactly one group (live values are documented in their own section).
GROUPS: dict[str, list[str]] = {
    "Sketch and loop": ["size", "resize_canvas", "full_screen", "run", "loop", "no_loop", "redraw", "is_looping",
                        "exit", "stop", "frame_rate", "show", "smooth", "no_smooth"],
    "Shapes": ["point", "line", "rect", "square", "ellipse", "circle", "triangle", "quad", "polygon", "arc",
               "rect_mode", "ellipse_mode"],
    "Curves and custom shapes": ["bezier", "bezier_point", "bezier_tangent", "curve", "curve_point", "curve_tangent",
                                 "curve_tightness", "begin_shape", "end_shape", "vertex", "bezier_vertex",
                                 "quadratic_vertex", "curve_vertex", "begin_contour", "end_contour"],
    "Colour": ["background", "clear", "color", "color_mode", "hsb", "hsl", "cmyk", "lerp_color", "linear_gradient",
               "radial_gradient"],
    "Fill and stroke": ["fill", "no_fill", "stroke", "no_stroke", "stroke_width", "stroke_cap", "stroke_join",
                        "miter_limit", "stroke_dash", "no_dash", "shadow", "no_shadow", "opacity", "blend_mode",
                        "erase", "no_erase", "tint", "no_tint"],
    "Text and fonts": ["text", "text_align", "text_ascent", "text_descent", "text_leading", "text_box", "text_path",
                       "text_to_points", "current_font", "text_size", "text_style", "text_tracking", "text_fallback",
                       "system_font", "text_features", "font_variations", "text_width", "fit_text_size", "text_on_path", "text_font",
                       "load_font"],
    "Transforms and the state stack": ["translate", "rotate", "scale", "shear_x", "shear_y", "apply_matrix",
                                       "reset_matrix", "push", "pop", "saved_state"],
    "Paths and clipping": ["path", "draw_path", "clip", "no_clip"],
    "Marks": ["mark"],
    "Play": ["variations", "keep"],
    "Pictures and layers": ["create_graphics", "layer", "hide_layer", "show_layer"],
    "Images and SVG": ["image", "image_mode", "load_image", "load_svg", "svg_paths"],
    "Pixels and filters": ["get", "set", "set_pixel", "load_pixels", "update_pixels", "filter", "apply_filter"],
    "Randomness and noise": ["random", "random_number", "random_choice", "random_gaussian", "random_seed", "noise", "noise_detail",
                             "noise_seed"],
    "Maths": ["constrain", "distance", "lerp", "map_range", "mag", "norm", "degrees", "radians"],
    "Time": ["year", "month", "day", "hour", "minute", "second", "millis"],
    "Interaction and controls": ["key_down", "cursor", "no_cursor", "create_button", "create_checkbox",
                                 "create_slider"],
    "Saving": ["save", "save_frames", "save_gif", "save_movie"],
    "Ground": ["area", "grid", "mm", "inch", "ground"],
    "Motion and pages": ["frame_duration", "new_page", "page_size", "page_count"],
    "Sound": ["load_sound", "create_sound", "tone", "note", "pluck", "melody", "sequence", "mix", "drone",
              "note_to_frequency", "frequency_to_note", "chord_notes"],
    "Music analysis and the microphone": ["microphone", "microphones"],
    "Camera": ["camera", "cameras", "load_clip"],
    "Drawing sound": ["draw_wave", "draw_spectrum", "spectrogram", "draw_pitch_line"],
    "Ragas and talas": ["ragas", "raga", "talas", "tala_info", "tala", "match_ragas"],
    "Classes": ["Vector", "FormattedString"],
    "Names for colours and options": ["COLORS", "CONSTANTS"],
}

# Which parameters take the words of each f.CONSTANTS group (D-103): (function or method, parameter). tests/test_constants.py
# checks each pair against the code that validates the words, in both directions, so this list cannot drift.
GROUP_PARAMS: dict[str, list[tuple[str, str]]] = {
    "MODE": [("rect_mode", "mode"), ("ellipse_mode", "mode"), ("image_mode", "mode")],
    "ARC": [("arc", "mode")],
    "COLOR_MODE": [("color_mode", "mode")],
    "ALIGN": [("text_align", "horizontal"), ("text_align", "vertical")],
    "STYLE": [("text_style", "style"), ("FormattedString.append", "style")],
    "CAP": [("stroke_cap", "cap"), ("PathBuilder.expand_stroke", "cap")],
    "JOIN": [("stroke_join", "join"), ("PathBuilder.expand_stroke", "join")],
    "CURSOR": [("cursor", "kind")],
    "BLEND": [("blend_mode", "mode")],
    "FILTER": [("filter", "kind"), ("apply_filter", "kind")],
    "WAVE": [("tone", "wave"), ("note", "wave"), ("melody", "wave")],
    "TUNING": [("melody", "tuning")],
    "ANCHOR": [("Mark.place", "anchor")],
    "MARK_STYLE": [("Mark.place", "style")],
    "SAVE_TEXT": [("save", "text"), ("Picture.save", "text")],
    "PROVIDERS": [("load_font", "provider")],
    "KEY": [("key_down", "key"), ("key", "value")],
    "MOUSE": [("mouse_button", "value")],
    "PAGE": [("size", "width"), ("new_page", "width"), ("page_size", "name")],
}
# The sentences that already explain the words of a group (the S-179 tables), for completions.json and API.md.
GROUP_MEANINGS: dict[str, list[dict[str, str]]] = {
    "ALIGN": [Sketch.TEXT_ALIGNS, Sketch.TEXT_VALIGNS], "STYLE": [typography.STYLE_MEANINGS],
    "CAP": [Sketch.STROKE_CAPS], "JOIN": [Sketch.STROKE_JOINS], "CURSOR": [CURSOR_KINDS],
    "BLEND": [Sketch.BLEND_MODES], "FILTER": [FILTER_KINDS], "WAVE": [synth.WAVES],
    "ANCHOR": [marks.ANCHOR_MEANINGS], "KEY": [KEY_NAMES],
}


def group_used_by(group: str) -> list[str]:
    """The functions that take a group's words (a live value such as f.key is written without a call)."""
    names: list[str] = []
    for function, parameter in GROUP_PARAMS[group]:
        label = function if parameter != "value" else f"f.{function}"
        if label not in names:
            names.append(label)
    return names


def word_meaning(group: str, word: str) -> str | None:
    """The sentence that explains *word* in *group*, or None. text_align's "center" has two (across, up and down)."""
    found = [table[word] for table in GROUP_MEANINGS.get(group, []) if word in table]
    if len(found) == 2:
        return f"Across: {found[0]} Up and down: {found[1]}"
    return found[0] if found else None


def slug_of(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


# ---------------------------------------------------------------- docstring parsing
# Option words with their meanings, printed under the function that takes them (D-092). Each table lives in the
# code that checks the word, so a word cannot be accepted without being explained (tests/test_api_docs.py).
WORD_MEANINGS: dict[str, list[tuple[str, dict[str, str]]]] = {
    "f.blend_mode": [("mode", Sketch.BLEND_MODES)],
    "f.stroke_cap": [("cap", Sketch.STROKE_CAPS)],
    "f.stroke_join": [("join", Sketch.STROKE_JOINS)],
    "PathBuilder.expand_stroke": [("cap", Sketch.STROKE_CAPS), ("join", Sketch.STROKE_JOINS)],
    "f.text_align": [("horizontal", Sketch.TEXT_ALIGNS), ("vertical", Sketch.TEXT_VALIGNS)],
    "f.text_style": [("style", typography.STYLE_MEANINGS)],
    "FormattedString.append": [("style", typography.STYLE_MEANINGS)],
    "f.filter": [("kind", FILTER_KINDS)],
    "f.apply_filter": [("kind", FILTER_KINDS)],
    "f.cursor": [("kind", CURSOR_KINDS)],
    "f.key_down": [("key", KEY_NAMES)],
    "f.tone": [("wave", synth.WAVES)],
    "f.note": [("wave", synth.WAVES)],
    "f.melody": [("wave", synth.WAVES)],
    "Mark.place": [("anchor", marks.ANCHOR_MEANINGS)],
}

HEADER = re.compile(r"^(Arguments|Returns|Raises|Example):\s*$")
SEE_ALSO = re.compile(r"^See also:\s*(.*)$")


def parse_doc(doc: str | None) -> dict:
    """Split a docstring into summary, prose, sections, see-also. Missing sections are empty."""
    result = {"summary": "", "prose": "", "Arguments": "", "Returns": "", "Raises": "", "Example": "", "see": []}
    if not doc:
        return result
    lines = inspect.cleandoc(doc).splitlines()
    current = "prose"
    buckets: dict[str, list[str]] = {"prose": []}
    for line in lines:
        m = HEADER.match(line)
        s = SEE_ALSO.match(line)
        if m:
            current = m.group(1)
            buckets[current] = []
        elif s:
            result["see"] = [n.strip().rstrip(".") for n in s.group(1).split(",") if n.strip()]
            current = "see"
        elif current != "see":
            buckets[current].append(line)
    prose = "\n".join(buckets["prose"]).strip("\n")
    first, _, rest = prose.partition("\n\n")
    result["summary"] = " ".join(first.split())
    result["prose"] = rest.strip()
    for name in SECTIONS:
        result[name] = textwrap.dedent("\n".join(buckets.get(name, []))).strip("\n")
    return result


def parse_arguments(body: str) -> list[tuple[list[str], str]]:
    """Entries 'x, y: text' at the section's left margin; deeper-indented lines continue the text."""
    entries: list[tuple[str, list[str]]] = []
    for line in body.splitlines():
        if not line.strip():
            continue
        if line[0] != " " and ":" in line:
            names, _, text = line.partition(":")
            entries.append((names, [text.strip()]))
        elif entries:
            entries[-1][1].append(line.strip())
    return [([n.strip().lstrip("*") for n in names.split(",") if n.strip()], " ".join(t for t in text if t))
            for names, text in entries]


def documented_params(doc: str | None) -> set[str]:
    out: set[str] = set()
    for names, _ in parse_arguments(parse_doc(doc)["Arguments"]):
        out.update(names)
    return out


# ---------------------------------------------------------------- class helpers
def class_names() -> list[str]:
    """The entries of api_classes.txt (module.ClassName per line)."""
    if not CLASS_LIST.exists():
        return []
    return [ln.strip() for ln in CLASS_LIST.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]


def resolve_class(entry: str):
    module, _, name = entry.rpartition(".")
    for candidate in (f"funground.{module}", module):
        try:
            return getattr(importlib.import_module(candidate), name)
        except (ImportError, AttributeError):
            continue
    raise SystemExit(f"api_classes.txt: cannot find {entry!r}")


def all_classes() -> list[tuple[str, type]]:
    """(name, class) for every class in api_classes.txt, then any public class not already there."""
    found: list[tuple[str, type]] = []
    seen: set[type] = set()
    for entry in class_names():
        cls = resolve_class(entry)
        if cls not in seen:
            seen.add(cls)
            found.append((cls.__name__, cls))
    for name in f._PUBLIC_NAMES:
        obj = getattr(f, name, None) if name not in _api.LIVE_NAMES else None
        if inspect.isclass(obj) and obj not in seen and name not in NAMESPACE_NAMES:
            seen.add(obj)
            found.append((obj.__name__, obj))
    return found


def public_members(cls: type) -> list[tuple[str, object]]:
    """Public methods and properties, own and inherited (not from object), sorted by name."""
    out: dict[str, object] = {}
    for klass in reversed(cls.__mro__):
        if klass is object:
            continue
        for name, value in vars(klass).items():
            if name.startswith("_"):
                continue
            if isinstance(value, (staticmethod, classmethod)):
                value = value.__func__
            if inspect.isfunction(value) or isinstance(value, property):
                out[name] = value
    return sorted(out.items())


# ---------------------------------------------------------------- rendering
def esc(text: str) -> str:
    return text.replace("|", "\\|")


# The Literal aliases of funground/_options.py are named for the code; a learner reads the group of f.CONSTANTS that
# holds the same words (tests/test_api_docs.py checks every alias has its group).
ALIAS_GROUP = {"RectMode": "MODE", "EllipseMode": "MODE", "ImageMode": "MODE", "ArcMode": "ARC", "ColorMode": "COLOR_MODE",
               "BlendMode": "BLEND", "TextAlignX": "ALIGN", "TextAlignY": "ALIGN", "TextStyle": "STYLE",
               "StrokeCap": "CAP", "StrokeJoin": "JOIN", "CursorKind": "CURSOR", "FilterKind": "FILTER", "Wave": "WAVE",
               "Tuning": "TUNING", "MarkAnchor": "ANCHOR", "MarkStyle": "MARK_STYLE", "SaveText": "SAVE_TEXT",
               "Provider": "PROVIDERS",
               "KeyName": "KEY", "PageName": "PAGE"}


def learner_types(text: str) -> str:
    """A signature with each option alias written as its group: ``mode: RectMode`` becomes ``mode: CONSTANTS.MODE``."""
    return re.sub(r"\b(" + "|".join(ALIAS_GROUP) + r")\b", lambda m: "CONSTANTS." + ALIAS_GROUP[m.group(1)], text)


def signature_text(prefix: str, name: str, obj, drop_first: bool = False) -> str:
    if not callable(obj):                                  # a value such as f.ground: its name alone
        return f"{prefix}{name}"
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):
        return f"{prefix}{name}(...)"
    params = list(sig.parameters.values())
    if drop_first and params and params[0].name in ("self", "cls"):
        params = params[1:]
    sig = sig.replace(parameters=params)
    text = re.sub(r"<object object at 0x[0-9A-Fa-f]+>", "<not given>", f"{prefix}{name}{sig}")   # a sentinel default
    return learner_types(re.sub(r" at 0x[0-9A-Fa-f]+", "", text))                               # keep it deterministic


class Page:
    def __init__(self) -> None:
        self.out: list[str] = []

    def add(self, *lines: str) -> None:
        self.out.extend(lines)

    def text(self) -> str:
        return "\n".join(self.out).rstrip("\n") + "\n"


def see_also(names: list[str], known: set[str], owner: tuple[str, set[str]] | None = None) -> str:
    """The See also line. In a class member's entry (*owner* is (class name, its member names)), a name is
    looked for in the class first, so Sound.play links to Sound.play and not to an f. function."""
    parts = []
    for n in names:
        if owner is not None and n in owner[1]:
            parts.append(f"[`{n}`](#cls-{owner[0]}-{n})")
        elif n in known:
            kind = "const" if n in NAMESPACE_NAMES else "cls" if inspect.isclass(getattr(f, n, None)) else "fn"
            parts.append(f"[`{n}`](#{kind}-{n})")
        else:
            parts.append(f"`{n}`")
    return "See also: " + ", ".join(parts) + "."


def add_since(page: Page, version: str | None) -> None:
    """The badge "Since 0.2." right under the heading of a name that is not in the first release (S-229), where a
    reader looking for the name sees it first."""
    if version:
        page.add(since.api_badge(version), "")


def render_entry(page: Page, anchor: str, heading: str, sig: str, doc: str | None, known: set[str],
                 level: str = "###", owner: tuple[str, set[str]] | None = None, arrives: str | None = None) -> None:
    d = parse_doc(doc)
    page.add(f'<a id="{anchor}"></a>', f"{level} {heading}", "")
    add_since(page, arrives)
    page.add("```py", sig, "```", "")
    page.add(d["summary"] or "*(no documentation yet)*", "")
    if d["prose"]:
        page.add(d["prose"], "")
    if d["Arguments"]:
        page.add("| Argument | Meaning |", "|---|---|")
        for names, text in parse_arguments(d["Arguments"]):
            page.add(f"| {', '.join('`' + n + '`' for n in names)} | {esc(text)} |")
        page.add("")
    for argument, meanings in WORD_MEANINGS.get(heading.strip("`"), []):
        page.add(f"**The words for `{argument}`.**", "", "| Word | What it does |", "|---|---|")
        for word, meaning in meanings.items():
            arrives_word = since.word_since(heading.strip("`").removeprefix("f."), argument, word)
            page.add(f'| `"{word}"` | {esc(meaning)}' + (f" ({since.api_line(arrives_word)})" if arrives_word else "") + " |")
        page.add("")
    if d["Returns"]:
        page.add("**Returns.** " + " ".join(d["Returns"].split()), "")
    if d["Raises"]:
        page.add("**Raises.**", "")
        for names, text in parse_arguments(d["Raises"]):
            page.add(f"- `{', '.join(names)}`: {text}")
        page.add("")
    if d["Example"]:
        page.add("```py", d["Example"], "```", "")
    if d["see"]:
        page.add(see_also(d["see"], known, owner), "")


def table(page: Page, headers: list[str], rows: list[list]) -> None:
    page.add("| " + " | ".join(headers) + " |", "|" + "---|" * len(headers))
    for row in rows:
        page.add("| " + " | ".join(esc(str(c)) for c in row) + " |")
    page.add("")


def code_list(items) -> str:
    return ", ".join(f"`{i}`" for i in items)


def hex_of(rgba: tuple[int, int, int, int]) -> str:
    r, g, b, a = rgba
    return f"#{r:02x}{g:02x}{b:02x}" + ("" if a == 255 else f"{a:02x}")


# The names of the environment variables are found in the source; these one-line meanings are written here.
ENV_NOTES = {
    "FUNGROUND_HEADLESS": "Set to 1, true or yes to run with no window (tests, servers, saving pictures).",
    "FUNGROUND_RENDERER": "Which drawing engine to use. Only `cairo` exists today, and it is the default.",
    "FUNGROUND_BACKING_SCALE": "Force the pixel-density scale of the window's backing store (a number).",
    "FUNGROUND_HIGHDPI": "Set to 1, true or yes to ask for a sharper window on a high-density screen.",
    "SDL_VIDEODRIVER": "Read from pygame's own setting. `dummy` means no real window.",
    "WAYLAND_DISPLAY": "Read to detect a Wayland desktop on Linux.",
}


def environment_variables() -> list[str]:
    found: set[str] = set()
    for path in sorted((ROOT / "funground").rglob("*.py")):
        found.update(re.findall(r"os\.environ\.get\(\s*[\"']([A-Z_0-9]+)[\"']", path.read_text(encoding="utf-8")))
    return sorted(found)


def reference_tables(page: Page) -> None:
    page.add('<a id="constants-and-reference-tables"></a>', "## Constants and reference tables", "",
             "Every table here is generated from the funground source, so it cannot drift from the code.", "")
    page.add("### Fixed words", "")
    rows = [
        ["`f.blend_mode(mode)`", code_list(Sketch.BLEND_MODES)],
        ["`f.stroke_cap(cap)`", code_list(Sketch.STROKE_CAPS)],
        ["`f.stroke_join(join)`", code_list(Sketch.STROKE_JOINS)],
        ["`f.text_align(horizontal, vertical)`, horizontal", code_list(Sketch.TEXT_ALIGNS)],
        ["`f.text_align(horizontal, vertical)`, vertical", code_list(Sketch.TEXT_VALIGNS)],
        ["`f.text_style(style)`", code_list(typography.TEXT_STYLES)],
        ["`f.color_mode(mode)`", code_list(_color.COLOR_MODES)],
        ["`f.cursor(kind)`", code_list(CURSOR_KINDS)],
        ["`f.filter(kind)`", code_list(FILTER_KINDS)],
        ["`f.save(path, text=...)`, text", code_list(TEXT_MODES)],
        ["Sound waves", code_list(synth.WAVES)],
    ]
    table(page, ["Where it is used", "Accepted words"], rows)

    page.add("### Colour modes and ranges", "",
             "The default range of each colour channel in each mode (first, second, third, alpha).", "")
    rows = [[f"`{m}`"] + [f"{v:g}" for v in rng] for m, rng in zip(_color.COLOR_MODES, _color.DEFAULT_COLOR_RANGES)]
    table(page, ["Mode", "First", "Second", "Third", "Alpha"], rows)

    page.add("### Keys and the mouse", "",
             "`f.key` is a single character such as `\"a\"`, or one of these names. "
             "`f.mouse_button` is one of the buttons below.", "")
    table(page, ["Kind", "Names"], [["Key names", code_list(KEY_NAMES)], ["Mouse buttons", code_list(MOUSE_BUTTONS)],
                                    ["Callbacks you can define", code_list(CALLBACK_NAMES)]])

    page.add("### Page sizes", "", "For `f.page_size(name)`, in points (1/72 inch). Any capitals are accepted.", "")
    table(page, ["Name", "Width", "Height"], [[f"`{n}`", w, h] for n, (w, h) in pages.PAGE_SIZES.items()])

    page.add("### Files", "")
    table(page, ["Function", "Formats"], [
        ["`f.save(path)`", code_list("." + x for x in FORMATS)],
        ["`f.save_gif`, `f.save_movie`", code_list("." + x for x in MOTION_FORMATS)],
    ])

    page.add("### Notes, sargam and chords", "")
    letters = "".join(synth._SEMITONES)
    page.add(f"- **Note names:** a letter from `{letters}`, an optional `#` or `b`, then an octave number, "
             f"such as `C4`, `F#3` or `Bb2`. The twelve names in an octave are {code_list(analysis.NOTE_NAMES)}.",
             "- **Sargam** (for `sa=`): a swara letter, then `'` for each octave up or `,` for each octave down. "
             "Lower-case letters are komal, and capital `M` is tivra Ma. The swaras, with their just-intonation "
             "ratio above Sa, are:", "")
    table(page, ["Swara", "Ratio from Sa"],
          [[f"`{s}`", str(Fraction(r).limit_denominator(100))] for s, r in zip(synth.SARGAM, synth.JUST_RATIOS)])
    page.add("- **Chord names** (for `f.chord_notes`): a note name then a suffix. Suffixes and their semitones:", "")
    table(page, ["Suffix", "Semitones above the root"],
          [[f"`{q or '(none)'}`", " ".join(map(str, st))] for q, st in analysis.CHORD_QUALITIES.items()])

    data = json.loads((ROOT / "funground" / "data" / "ragas.json").read_text(encoding="utf-8"))
    page.add("### Ragas", "", "From `f.ragas()` and `f.raga(name)`. See the "
             "[ragas and talas chapter](../guide/17_ragas_and_talas.md).", "")
    table(page, ["Name", "Thaat", "Time"], [[r["name"], r["thaat"], r["time"]] for r in data["ragas"]])
    page.add("### Talas", "", "From `f.talas()` and `f.tala_info(name)`.", "")
    table(page, ["Name", "Beats", "Vibhag (divisions)"],
          [[t["name"], t["beats"], "+".join(map(str, t["vibhag"]))] for t in data["talas"]])

    page.add("### Bundled fonts", "", "Files in `funground/fonts`, always available with no install.", "")
    fonts = sorted(p.name for p in (ROOT / "funground" / "fonts").glob("*.ttf"))
    styles = {v: k for k, v in typography.STYLE_FILES.items()}
    table(page, ["File", "Used for"],
          [[f"`{n}`", f"`f.text_style(\"{styles[n]}\")`" if n in styles else
            ("fallback for letters the font lacks" if n in typography.BUNDLED_FALLBACKS else "")] for n in fonts])

    page.add("### Environment variables", "")
    table(page, ["Variable", "Meaning"],
          [[f"`{v}`", ENV_NOTES.get(v, "(see the source)")] for v in environment_variables()])

    page.add('<a id="named-colours"></a>', "### Named colours", "",
             f"All {len(_colornames.NAMED_COLORS)} names accepted wherever a colour is expected, such as "
             "`f.fill(\"tomato\")`, with their hex values.", "")
    items = sorted(_colornames.NAMED_COLORS.items())
    per = 4
    page.add("| " + " | ".join(["Name | Hex"] * per) + " |", "|" + "---|---|" * per)
    for i in range(0, len(items), per):
        cells: list[str] = []
        for n, rgba in items[i:i + per]:
            cells += [f"`{n}`", f"`{hex_of(rgba)}`"]
        cells += [""] * (2 * per - len(cells))
        page.add("| " + " | ".join(cells) + " |")
    page.add("")


def render_namespace(page: Page, name: str, known: set[str]) -> None:
    """The entry for f.COLORS or f.CONSTANTS: what it is, how to use it, and its members."""
    cls = getattr(f, name)
    d = parse_doc(cls.__doc__)
    example = 'f.COLORS.TOMATO  # "tomato"' if name == "COLORS" else 'f.CONSTANTS.ALIGN.CENTER  # "center"'
    page.add(f'<a id="const-{name}"></a>', f"### `f.{name}`", "")
    add_since(page, since.name_since(name))
    page.add("```py", example, "```", "", d["summary"], "")
    if d["prose"]:
        page.add(d["prose"], "")
    if name == "COLORS":
        page.add(f"There is one name for each of the {len(cls)} named colours. The name is the colour in capitals and "
                 'its value is the colour name, so `f.COLORS.TOMATO == "tomato"`. The '
                 "[named colours table](#named-colours) lists every colour with its hex value; write its name in "
                 "capitals. Iterate it for all the names: `list(f.COLORS)`.", "")
    else:
        page.add(f"There are {len(cls)} groups. Each is named after what it chooses and holds the words that choice "
                 "accepts. Iterate a group for its words: `list(f.CONSTANTS.BLEND)`. Words can mean different things in "
                 "different groups: `LEFT` is a text alignment, a key and a mouse button.", "")
        for group, members in cls._members.items():
            summary = parse_doc(members.__doc__)["summary"]
            page.add(f'<a id="const-{name}-{group}"></a>', f"#### `f.CONSTANTS.{group}`", "",
                     f"{summary} Used by: {code_list(group_used_by(group))}.", "")
            rows = [[f"`{n}`", f'`"{v}"`', word_meaning(group, v) or ""] for n, v in members._members.items()]
            table(page, ["Name", "Word", "What it does"], rows)
    if d["Example"]:
        page.add("```py", d["Example"], "```", "")
    if d["see"]:
        page.add(see_also(d["see"], known), "")


def check_groups() -> None:
    all_names = list(f._PUBLIC_NAMES)
    live = set(_api.LIVE_NAMES)
    grouped = [n for names in GROUPS.values() for n in names]
    errors = []
    dup = sorted({n for n in grouped if grouped.count(n) > 1})
    if dup:
        errors.append(f"in more than one group: {dup}")
    missing = sorted(set(all_names) - set(grouped) - live)
    if missing:
        errors.append(f"in funground._PUBLIC_NAMES but in no group (add them to GROUPS): {missing}")
    extra = sorted(set(grouped) - set(all_names))
    if extra:
        errors.append(f"in a group but not in funground._PUBLIC_NAMES: {extra}")
    if errors:
        raise SystemExit("make_api_reference: " + "; ".join(errors))


def build() -> str:
    check_groups()
    live = set(_api.LIVE_NAMES)
    live_docs = getattr(_api, "LIVE_DOCS", {})
    known = {n for names in GROUPS.values() for n in names}
    classes = all_classes()
    class_set = {n for n, _ in classes}

    p = Page()
    p.add("# funground API reference", "",
          "Every public name in funground, with its signature, arguments and an example. "
          "This page is generated from the docstrings in the code, so `help(f.name)` in Python shows the same text. "
          "Do not edit it by hand: change the docstring and run `python tools/make_api_reference.py`.", "",
          "Related pages: the [Quick Reference](Quick_Reference.md) (every function by topic, with pictures), "
          "the [guide](../guide/README.md) (learn step by step), "
          "[When something goes wrong](../guide/errors.md), the [glossary](../guide/glossary.md), "
          "[funground compared with p5 and DrawBot](Compared_with_p5_and_DrawBot.md) "
          "and the [documentation front door](../README.md).", "",
          "In the examples, `import funground as f` is understood.", "", "## Contents", "")
    for title, names in GROUPS.items():
        p.add(f"- [{title}](#{slug_of(title)}): "
              + ", ".join(f"[`{n}`](#{'const-' if n in NAMESPACE_NAMES else 'cls-' if n in class_set else 'fn-'}{n})"
                      for n in names))
    p.add("- [Live values](#live-values): " + ", ".join(f"[`{n}`](#live-{n})" for n in sorted(live)))
    p.add("- [Classes in detail](#classes-in-detail): " + ", ".join(f"[`{n}`](#cls-{n})" for n, _ in classes))
    p.add("- [Constants and reference tables](#constants-and-reference-tables)", "")

    for title, names in GROUPS.items():
        p.add(f'<a id="{slug_of(title)}"></a>', f"## {title}", "")
        for name in names:
            obj = getattr(f, name)
            if name in NAMESPACE_NAMES:
                render_namespace(p, name, known)
                continue
            if inspect.isclass(obj):
                p.add(f"- `{name}`: see [the {name} class](#cls-{name}).", "")
                continue
            render_entry(p, f"fn-{name}", f"`f.{name}`", signature_text("f.", name, obj), obj.__doc__, known,
                         arrives=since.name_since(name))

    p.add('<a id="live-values"></a>', "## Live values", "",
          "These look like variables. Read them as `f.width`, `f.mouse_x` and so on. "
          "They always hold the current value, and you cannot set them.", "")
    for name in sorted(live):
        d = parse_doc(live_docs.get(name))
        p.add(f'<a id="live-{name}"></a>', f"### `f.{name}`", "")
        add_since(p, since.name_since(name))
        p.add(d["summary"] or "*(no documentation yet)*", "")
        if d["prose"]:
            p.add(d["prose"], "")
        if d["Returns"]:
            p.add("**Value.** " + " ".join(d["Returns"].split()), "")
        if d["Example"]:
            p.add("```py", d["Example"], "```", "")
        if d["see"]:
            p.add(see_also(d["see"], known), "")

    p.add('<a id="classes-in-detail"></a>', "## Classes in detail", "")
    if not classes:
        p.add("*(The class list, docs/reference/api_classes.txt, is not written yet.)*", "")
    for name, cls in classes:
        try:
            sig = signature_text("", name, cls)
        except Exception:
            sig = f"{name}(...)"
        d = parse_doc(cls.__doc__)
        p.add(f'<a id="cls-{name}"></a>', f"### `{name}`", "")
        add_since(p, since.class_since(name))
        p.add("```py", sig, "```", "", d["summary"] or "*(no documentation yet)*", "")
        if d["prose"]:
            p.add(d["prose"], "")
        if d["Arguments"]:
            p.add("| Argument | Meaning |", "|---|---|")
            for names, text in parse_arguments(d["Arguments"]):
                p.add(f"| {', '.join('`' + n + '`' for n in names)} | {esc(text)} |")
            p.add("")
        if d["Example"]:
            p.add("```py", d["Example"], "```", "")
        members = public_members(cls)
        owner = (name, {mname for mname, _ in members})
        for mname, member in members:
            anchor = f"cls-{name}-{mname}"
            if isinstance(member, property):
                render_entry(p, anchor, f"`{name}.{mname}`", f"{name}.{mname}  # property", member.fget.__doc__,
                             known, level="####", owner=owner, arrives=since.member_since(name, mname))
            else:
                render_entry(p, anchor, f"`{name}.{mname}`", signature_text(f"{name}.", mname, member, True),
                             member.__doc__, known, level="####", owner=owner,
                             arrives=since.member_since(name, mname))

    reference_tables(p)
    return p.text()


# ---- the pages for AI assistants (S-129)

ANCHOR_LINE = re.compile(r'^<a id="[^"]*"></a>\n', re.M)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def absolute_links(text: str, folder: str) -> str:
    """Links that work outside the repository: an in-page anchor becomes plain text, a relative path an
    address on GitHub (folder is where the text lives, such as "docs/reference")."""
    def fix(match: re.Match) -> str:
        label, target = match.groups()
        if target.startswith("#"):
            return label
        if re.match(r"[a-z]+:", target):
            return match.group(0)
        path = Path(folder, target.split("#")[0]).as_posix()
        parts: list[str] = []
        for part in path.split("/"):
            if part == "..":
                parts.pop()
            elif part not in ("", "."):
                parts.append(part)
        return f"[{label}]({REPO_URL}{'/'.join(parts)})"
    return LINK.sub(fix, text)


def rules_text() -> str:
    """The hand-written rules, with their headings one level down, so they sit under the page's own."""
    rules = RULES.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    return re.sub(r"^## ", "### ", rules, flags=re.M)


def llms_index() -> str:
    lines = ["# funground", "", f"> {LLMS_SUMMARY}", "", rules_text(), "", "## Docs", ""]
    lines += [f"- [{title}]({REPO_URL}{path}): {note}" for title, path, note in LLMS_LINKS]
    lines += ["", "## Optional", "",
              f"- [llms-full.txt]({REPO_URL}llms-full.txt): these rules and the whole API reference in one file", ""]
    return "\n".join(lines)


def llms_full(api: str) -> str:
    """The rules, then API.md without its title, its anchors and its relative links, every heading one level down."""
    body = api.split("\n", 1)[1]
    body = absolute_links(ANCHOR_LINE.sub("", body), "docs/reference")
    body = re.sub(r"^(#{2,5}) ", r"#\1 ", body, flags=re.M)
    return "\n".join(["# funground", "", f"> {LLMS_SUMMARY}", "", "## Rules for writing funground code", "",
                      rules_text(), "", "## The API reference", "", body.strip(), ""])


# ---- the list of names an editor suggests (S-195, D-102)

def first_sentence(summary: str) -> str:
    """The summary up to its first full stop that ends a sentence."""
    m = re.search(r"[.!?](?=\s|$)", summary)
    return summary[:m.end()] if m else summary


def declared_value_types() -> dict[str, str]:
    """The type of each live value, as declared under TYPE_CHECKING in funground/__init__.py."""
    tree = ast.parse((ROOT / "funground" / "__init__.py").read_text(encoding="utf-8"))
    types: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.If) and ast.unparse(node.test) == "TYPE_CHECKING":
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    types[item.target.id] = ast.unparse(item.annotation)
    return types


def learner_signature(name: str, obj, drop_first: bool = False) -> tuple[str, str, list[str]]:
    """(what a learner reads, with types, the names of the parameters typed as a colour) for a function, a class or,
    with *drop_first*, a method (its ``self`` is left out)."""
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):
        return f"{name}(...)", "(...)", []
    params = list(sig.parameters.values())
    if drop_first and params and params[0].name in ("self", "cls"):
        sig = sig.replace(parameters=params[1:])
    if inspect.isclass(obj):                                # a class's signature has no return type
        sig = sig.replace(return_annotation=inspect.Signature.empty)
    plain, colour = [], []
    for p in sig.parameters.values():
        star = {p.VAR_POSITIONAL: "*", p.VAR_KEYWORD: "**"}.get(p.kind, "")
        default = "" if p.default is p.empty else "=" + re.sub(r"<object object at 0x[0-9A-Fa-f]+>", "<not given>", repr(p.default))
        plain.append(f"{star}{p.name}{default}")
        if isinstance(p.annotation, str) and re.search(r"\bColor\b", p.annotation):
            colour.append(p.name)
    detail = re.sub(r" at 0x[0-9A-Fa-f]+", "", re.sub(r"<object object at 0x[0-9A-Fa-f]+>", "<not given>", str(sig)))
    return f"{name}({', '.join(plain)})", learner_types(detail.replace("'", "").replace('"', "")), colour


def namespace_members(name: str) -> list[dict]:
    """The members of f.COLORS (name, value, hex) or f.CONSTANTS (each group with its words)."""
    if name == "COLORS":
        return [{"name": n, "value": v, "hex": hex_of(_colornames.NAMED_COLORS[v])[:7]}
                for n, v in f.COLORS._members.items()]
    groups = []
    for group, members in f.CONSTANTS._members.items():
        words = []
        for n, v in members._members.items():
            word = {"name": n, "value": v}
            meaning = word_meaning(group, v)
            if meaning:
                word["meaning"] = meaning
            words.append(word)
        groups.append({"name": group, "used_by": group_used_by(group), "members": words})
    return groups


def returned_class(annotation, doc: str | None, class_set: set[str]) -> str | None:
    """The documented class a function or method gives back, or None. The return annotation says it
    (``-> "PathBuilder"``, ``-> Clip | None``); without one, the Returns text must begin "a new Picture"."""
    if isinstance(annotation, str):
        found = annotation.replace("'", "").replace('"', "").split("|")[0].strip()
    else:
        found = re.match(r"(?:an?|the)(?: new| same)? ([A-Z]\w*)", " ".join(parse_doc(doc)["Returns"].split()))
        found = found.group(1) if found else ""
    return found if found in class_set else None


def class_members(cls: type, class_set: set[str]) -> list[dict]:
    """The methods and properties of a class, as editors suggest them after ``object.`` (the order of the reference)."""
    members = []
    for name, member in public_members(cls):
        is_property = isinstance(member, property)
        function = member.fget if is_property else member
        annotation = inspect.signature(function).return_annotation
        entry: dict = {"name": name, "kind": "property" if is_property else "method"}
        if is_property:
            kept = annotation if isinstance(annotation, str) else ""
            entry.update(signature=name, detail=learner_types(kept.replace("'", "").replace('"', "")))
        else:
            signature, detail, _ = learner_signature(name, function, True)
            entry.update(signature=signature, detail=detail)
        entry.update(summary=first_sentence(parse_doc(function.__doc__)["summary"]),
                     url=f"reference/API.md#cls-{cls.__name__}-{name}")
        returns = returned_class(annotation, function.__doc__, class_set)
        if returns:
            entry["returns"] = returns
        if since.member_since(cls.__name__, name):
            entry["since"] = since.member_since(cls.__name__, name)
        members.append(entry)
    return members


def completions_text() -> str:
    """funground/completions.json: every public name with its signature, summary and link, the option words,
    the named colours, the parameters that take a colour and the members of every documented class."""
    check_groups()
    class_set = {n for n, _ in all_classes()}
    live_docs = getattr(_api, "LIVE_DOCS", {})
    value_types = declared_value_types()
    star_out = set(f.STAR_LEAVES_OUT)
    words: dict[str, dict] = {}
    for key, tables in WORD_MEANINGS.items():
        if key.startswith("f."):
            words[key[2:]] = {arg: [{"word": w, "meaning": m, **({"since": v} if (v := since.word_since(key[2:], arg, w)) else {})}
                                    for w, m in table.items()] for arg, table in tables}
    names, color_params = [], []
    for name in f._PUBLIC_NAMES:
        entry: dict = {"name": name}
        if name in NAMESPACE_NAMES:
            cls = getattr(f, name)
            detail = f"{len(cls)} colours" if name == "COLORS" else f"{len(cls)} groups of words"
            entry.update(kind="namespace", signature=name, detail=detail,
                         summary=first_sentence(parse_doc(cls.__doc__)["summary"]), url=f"reference/API.md#const-{name}")
            entry["members"] = namespace_members(name)
        elif name in _api.LIVE_NAMES:
            entry.update(kind="value", signature=name, detail=value_types[name],
                         summary=first_sentence(parse_doc(live_docs.get(name))["summary"]), url=f"reference/API.md#live-{name}")
        else:
            obj = getattr(f, name)
            is_class = inspect.isclass(obj)
            signature, detail, colour = learner_signature(name, obj)
            entry.update(kind="class" if is_class else "function", signature=signature, detail=detail,
                         summary=first_sentence(parse_doc(obj.__doc__)["summary"]),
                         url=f"reference/API.md#{'cls' if is_class else 'fn'}-{name}")
            color_params += [{"function": name, "parameter": p} for p in colour]
            returns = None if is_class else returned_class(inspect.signature(obj).return_annotation, obj.__doc__, class_set)
            if returns:
                entry["returns"] = returns
        if since.name_since(name):
            entry["since"] = since.name_since(name)
        entry["star"] = name not in star_out
        if name in words:
            entry["options"] = words[name]
        names.append(entry)
    colors = [{"name": n, "hex": hex_of(rgba)[:7]} for n, rgba in sorted(_colornames.NAMED_COLORS.items())]
    classes = {name: {"summary": first_sentence(parse_doc(cls.__doc__)["summary"]), "url": f"reference/API.md#cls-{name}",
                      **({"since": since.class_since(name)} if since.class_since(name) else {}),
                      "members": class_members(cls, class_set)} for name, cls in all_classes()}
    data = {"version": f.__version__, "names": names, "colors": colors, "color_params": color_params, "classes": classes}
    return json.dumps(data, indent=1, ensure_ascii=False) + "\n"


def colors_class_text() -> str:
    """funground/_color_names_class.py: the class f.COLORS, one ``NAME: Final = "name"`` line for each named colour."""
    lines = ['"""f.COLORS: a name for every named colour (D-103, S-174).', "",
             "Generated by tools/make_api_reference.py from funground/_colornames.py. Generated, do not edit.", '"""',
             "from __future__ import annotations", "", "from typing import Final", "",
             "from ._namespaces import _NamespaceMeta", "", "",
             "class COLORS(metaclass=_NamespaceMeta):",
             '    """Names for the named colours: ``f.COLORS.TOMATO`` is the word ``"tomato"``.',
             "",
             '    Write whichever you like: ``f.fill(f.COLORS.TOMATO)`` and ``f.fill("tomato")`` do the same. After',
             "    ``from funground import *`` write ``COLORS.TOMATO``. The list is fixed: you cannot add to it or change",
             "    it. Every name is written in capitals, so the colour ``antiquewhite1`` is ``ANTIQUEWHITE1``.",
             "", "    Example:", "        f.fill(f.COLORS.TOMATO)", "", "    See also: fill, background, stroke, CONSTANTS",
             '    """', ""]
    lines += [f'    {name.upper()}: Final = "{name}"' for name in sorted(_colornames.NAMED_COLORS)]
    return "\n".join(lines) + "\n"


def outputs() -> dict[Path, str]:
    """Every generated page and its text. The two pages for assistants are written twice: at the root of
    the repository and inside the package (python -m pip install funground carries them). The list of
    suggestions for editors, funground/completions.json, is written with them."""
    api = build()
    pages = {OUT: api}
    for name, text in (("llms.txt", llms_index()), ("llms-full.txt", llms_full(api))):
        pages[ROOT / name] = text
        pages[ROOT / "funground" / name] = text
    pages[COMPLETIONS] = completions_text()
    pages[COLORS_CLASS] = colors_class_text()
    return pages


def main(argv: list[str]) -> int:
    pages = outputs()
    if "--check" in argv:
        stale = [path for path, text in pages.items()
                 if (path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else "") != text]
        for path in stale:
            print(f"{path.relative_to(ROOT).as_posix()} is out of date. Run: .venv/Scripts/python tools/make_api_reference.py")
        if not stale:
            print("docs/reference/API.md, llms.txt, llms-full.txt and completions.json are up to date.")
        return 1 if stale else 0
    for path, text in pages.items():
        path.write_bytes(text.encode("utf-8"))
        print(f"wrote {path.relative_to(ROOT).as_posix()} ({len(text.encode('utf-8'))} bytes)")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
