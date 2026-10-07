"""Generate docs/reference/API.md from the docstrings and the data tables in funground (D-066).

Run:    .venv/Scripts/python tools/make_api_reference.py
Check:  .venv/Scripts/python tools/make_api_reference.py --check     (exit 1 if API.md is out of date)

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
import inspect
import json
import re
import sys
import textwrap
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import funground as f  # noqa: E402
from funground import _colornames, api as _api, pages, synth  # noqa: E402
from funground import analysis, typography  # noqa: E402
_color = sys.modules["funground.color"]  # f.color (the function) hides the module as an attribute
from funground.export import FORMATS, TEXT_MODES  # noqa: E402
from funground.export.motion import MOTION_FORMATS  # noqa: E402
from funground.imaging import FILTER_KINDS  # noqa: E402
from funground.platform.base import CURSOR_KINDS, KEY_NAMES, MOUSE_BUTTONS  # noqa: E402
from funground.sketch import CALLBACK_NAMES, Sketch  # noqa: E402

OUT = ROOT / "docs" / "reference" / "API.md"
CLASS_LIST = ROOT / "docs" / "reference" / "api_classes.txt"

SECTIONS = ("Arguments", "Returns", "Raises", "Example")

# Every name in funground.__all__ must be in exactly one group (live values are documented in their own section).
GROUPS: dict[str, list[str]] = {
    "Sketch and loop": ["size", "resize_canvas", "full_screen", "run", "loop", "no_loop", "redraw", "is_looping",
                        "exit", "stop", "frame_rate", "show", "smooth", "no_smooth"],
    "Shapes": ["point", "line", "rect", "square", "ellipse", "circle", "triangle", "quad", "polygon", "arc",
               "rect_mode", "ellipse_mode"],
    "Curves and custom shapes": ["bezier", "bezier_point", "bezier_tangent", "curve", "curve_point", "curve_tangent",
                                 "curve_tightness", "begin_shape", "end_shape", "vertex", "bezier_vertex",
                                 "quadratic_vertex", "curve_vertex", "begin_contour", "end_contour"],
    "Colour": ["background", "clear", "color", "color_mode", "hsb", "hsl", "lerp_color", "linear_gradient",
               "radial_gradient"],
    "Fill and stroke": ["fill", "no_fill", "stroke", "no_stroke", "stroke_width", "stroke_cap", "stroke_join",
                        "miter_limit", "stroke_dash", "no_dash", "shadow", "no_shadow", "opacity", "blend_mode",
                        "erase", "no_erase", "tint", "no_tint"],
    "Text and fonts": ["text", "text_align", "text_ascent", "text_descent", "text_leading", "text_box", "text_path",
                       "text_to_points", "current_font", "text_size", "text_style", "text_tracking", "text_fallback",
                       "system_font", "text_features", "font_variations", "text_width", "text_font", "load_font"],
    "Transforms and the state stack": ["translate", "rotate", "scale", "shear_x", "shear_y", "apply_matrix",
                                       "reset_matrix", "push", "pop", "saved_state"],
    "Paths and clipping": ["path", "draw_path", "clip", "no_clip"],
    "Pictures and layers": ["create_graphics", "layer", "hide_layer", "show_layer"],
    "Images and SVG": ["image", "image_mode", "load_image", "load_svg", "svg_paths"],
    "Pixels and filters": ["get", "set", "load_pixels", "update_pixels", "filter"],
    "Randomness and noise": ["random", "random_choice", "random_gaussian", "random_seed", "noise", "noise_detail",
                             "noise_seed"],
    "Maths": ["constrain", "distance", "lerp", "map_range", "mag", "norm", "degrees", "radians"],
    "Time": ["year", "month", "day", "hour", "minute", "second", "millis"],
    "Interaction and controls": ["key_down", "cursor", "no_cursor", "create_button", "create_checkbox",
                                 "create_slider"],
    "Saving": ["save", "save_frames", "save_gif", "save_movie"],
    "Ground": ["grid", "mm", "inch", "ground"],
    "Motion and pages": ["frame_duration", "new_page", "page_size", "page_count"],
    "Sound": ["load_sound", "create_sound", "tone", "note", "pluck", "melody", "sequence", "mix", "drone",
              "note_to_frequency", "frequency_to_note", "chord_notes"],
    "Music analysis and the microphone": ["microphone", "microphones"],
    "Drawing sound": ["draw_wave", "draw_spectrum", "spectrogram", "draw_pitch_line"],
    "Ragas and talas": ["ragas", "raga", "talas", "tala_info", "tala", "match_ragas"],
    "Classes": ["Vector", "FormattedString"],
}


def slug_of(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


# ---------------------------------------------------------------- docstring parsing
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
    """(name, class) for every class in api_classes.txt, then any class in __all__ not already there."""
    found: list[tuple[str, type]] = []
    seen: set[type] = set()
    for entry in class_names():
        cls = resolve_class(entry)
        if cls not in seen:
            seen.add(cls)
            found.append((cls.__name__, cls))
    for name in f.__all__:
        obj = getattr(f, name, None) if name not in _api.LIVE_NAMES else None
        if inspect.isclass(obj) and obj not in seen:
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


def signature_text(prefix: str, name: str, obj, drop_first: bool = False) -> str:
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):
        return f"{prefix}{name}(...)"
    params = list(sig.parameters.values())
    if drop_first and params and params[0].name in ("self", "cls"):
        params = params[1:]
    sig = sig.replace(parameters=params)
    text = re.sub(r"<object object at 0x[0-9A-Fa-f]+>", "<not given>", f"{prefix}{name}{sig}")   # a sentinel default
    return re.sub(r" at 0x[0-9A-Fa-f]+", "", text)                                              # keep it deterministic


class Page:
    def __init__(self) -> None:
        self.out: list[str] = []

    def add(self, *lines: str) -> None:
        self.out.extend(lines)

    def text(self) -> str:
        return "\n".join(self.out).rstrip("\n") + "\n"


def see_also(names: list[str], known: set[str]) -> str:
    parts = []
    for n in names:
        if n in known:
            kind = "cls" if inspect.isclass(getattr(f, n, None)) else "fn"
            parts.append(f"[`{n}`](#{kind}-{n})")
        else:
            parts.append(f"`{n}`")
    return "See also: " + ", ".join(parts) + "."


def render_entry(page: Page, anchor: str, heading: str, sig: str, doc: str | None, known: set[str],
                 level: str = "###") -> None:
    d = parse_doc(doc)
    page.add(f'<a id="{anchor}"></a>', f"{level} {heading}", "", "```py", sig, "```", "")
    page.add(d["summary"] or "*(no documentation yet)*", "")
    if d["prose"]:
        page.add(d["prose"], "")
    if d["Arguments"]:
        page.add("| Argument | Meaning |", "|---|---|")
        for names, text in parse_arguments(d["Arguments"]):
            page.add(f"| {', '.join('`' + n + '`' for n in names)} | {esc(text)} |")
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
        page.add(see_also(d["see"], known), "")


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

    page.add("### Named colours", "",
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


def check_groups() -> None:
    all_names = list(f.__all__)
    live = set(_api.LIVE_NAMES)
    grouped = [n for names in GROUPS.values() for n in names]
    errors = []
    dup = sorted({n for n in grouped if grouped.count(n) > 1})
    if dup:
        errors.append(f"in more than one group: {dup}")
    missing = sorted(set(all_names) - set(grouped) - live)
    if missing:
        errors.append(f"in funground.__all__ but in no group (add them to GROUPS): {missing}")
    extra = sorted(set(grouped) - set(all_names))
    if extra:
        errors.append(f"in a group but not in funground.__all__: {extra}")
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
              + ", ".join(f"[`{n}`](#{'cls-' if n in class_set else 'fn-'}{n})" for n in names))
    p.add("- [Live values](#live-values): " + ", ".join(f"[`{n}`](#live-{n})" for n in sorted(live)))
    p.add("- [Classes in detail](#classes-in-detail): " + ", ".join(f"[`{n}`](#cls-{n})" for n, _ in classes))
    p.add("- [Constants and reference tables](#constants-and-reference-tables)", "")

    for title, names in GROUPS.items():
        p.add(f'<a id="{slug_of(title)}"></a>', f"## {title}", "")
        for name in names:
            obj = getattr(f, name)
            if inspect.isclass(obj):
                p.add(f"- `{name}`: see [the {name} class](#cls-{name}).", "")
                continue
            render_entry(p, f"fn-{name}", f"`f.{name}`", signature_text("f.", name, obj), obj.__doc__, known)

    p.add('<a id="live-values"></a>', "## Live values", "",
          "These look like variables. Read them as `f.width`, `f.mouse_x` and so on. "
          "They always hold the current value, and you cannot set them.", "")
    for name in sorted(live):
        d = parse_doc(live_docs.get(name))
        p.add(f'<a id="live-{name}"></a>', f"### `f.{name}`", "", d["summary"] or "*(no documentation yet)*", "")
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
        p.add(f'<a id="cls-{name}"></a>', f"### `{name}`", "", "```py", sig, "```", "",
              d["summary"] or "*(no documentation yet)*", "")
        if d["prose"]:
            p.add(d["prose"], "")
        if d["Arguments"]:
            p.add("| Argument | Meaning |", "|---|---|")
            for names, text in parse_arguments(d["Arguments"]):
                p.add(f"| {', '.join('`' + n + '`' for n in names)} | {esc(text)} |")
            p.add("")
        if d["Example"]:
            p.add("```py", d["Example"], "```", "")
        for mname, member in public_members(cls):
            anchor = f"cls-{name}-{mname}"
            if isinstance(member, property):
                render_entry(p, anchor, f"`{name}.{mname}`", f"{name}.{mname}  # property", member.fget.__doc__,
                             known, level="####")
            else:
                render_entry(p, anchor, f"`{name}.{mname}`", signature_text(f"{name}.", mname, member, True),
                             member.__doc__, known, level="####")

    reference_tables(p)
    return p.text()


def main(argv: list[str]) -> int:
    text = build()
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current.replace("\r\n", "\n") != text:
            print("docs/reference/API.md is out of date. Run: .venv/Scripts/python tools/make_api_reference.py")
            return 1
        print("docs/reference/API.md is up to date.")
        return 0
    OUT.write_bytes(text.encode("utf-8"))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
