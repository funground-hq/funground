"""check_originality.py -- an originality check for funground's example code (D-026).

funground's examples are published as CC0 (public domain). That is only honest if the
examples are our own written expression, not a copy or translation of an example from
another project. This tool compares our example code against a corpus of files pulled
from well-known creative-coding collections (p5.js, Processing, DrawBot, py5, pygame,
the Nature of Code, ...) and reports the closest match for each of our examples.

Because the collections are mostly JavaScript and Java and ours is Python, raw text is
not compared. Instead each file is reduced to four normalised fingerprints:

  - calls:       the ordered sequence of called function/method names. camelCase is
                  folded to snake_case and any receiver is dropped (`f.circle` and
                  `p5.createCanvas`/`createCanvas` both become a bare name). Scored by
                  the containment of 5-grams (the share of our 5-grams found in the
                  other file) and the longest common contiguous run of calls.
  - numbers:     the ordered numeric literals, ignoring 0, 1, 2 and common canvas sizes
                  (a copied sketch tends to keep its magic numbers). Scored by the
                  containment of 4-grams.
  - words:       the words in comments and string literals, lower-cased. Scored by the
                  longest common contiguous run (eight or more words in a row is a
                  strong signal on its own).
  - identifiers: the set of user-chosen names (variables, functions), excluding API
                  names and very common words. Scored by Jaccard similarity.

A pair is flagged when its combined score, or one strong single signal, crosses a
threshold. The thresholds are tuned against tests/test_check_originality.py so that a
faithful translation is flagged (even after renaming and re-commenting) and unrelated
sketches that merely share the vocabulary of the craft (setup, draw, background,
circle) are not.

What this cannot check: it only ever compares against the corpora it is given, so it
cannot see the whole web, books or videos; and it detects matching written expression
(the same calls, in the same order, with the same numbers or wording), not a matching
idea -- two people can write a bouncing ball, or a mover with velocity and gravity,
independently, and this tool will not flag that.

Usage:
    python tools/check_originality.py --corpus DIR [--corpus DIR2 ...] [--report FILE.md] [PATHS...]
    python tools/check_originality.py --fetch DIR
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# The pinned corpus list used by --fetch. Each entry is a shallow, sparse clone.
# ---------------------------------------------------------------------------

CORPORA = [
    {
        "name": "p5.js-website examples",
        "url": "https://github.com/processing/p5.js-website",
        "branch": "main",
        "paths": ["src/content/examples"],
        "licence": "MIT (repository LICENSE)",
    },
    {
        "name": "p5.js reference (@example code in src/)",
        "url": "https://github.com/processing/p5.js",
        "branch": "main",
        "paths": ["src"],
        "licence": "LGPL-2.1-or-later (repository LICENSE)",
    },
    {
        "name": "Processing examples",
        "url": "https://github.com/processing/processing-examples",
        "branch": "main",
        "paths": ["Basics", "Topics", "Demos"],
        "licence": "Public domain (Reas/Fry/Shiffman) or original author's copyright, per README",
    },
    {
        "name": "DrawBot examples and docs",
        "url": "https://github.com/typemytype/drawbot",
        "branch": "master",
        "paths": ["examples", "docs/content"],
        "licence": "BSD (license.txt)",
    },
    {
        "name": "py5 examples",
        "url": "https://github.com/py5coding/py5examples",
        "branch": "main",
        "paths": ["examples"],
        "licence": "MIT (LICENSE)",
    },
    {
        "name": "p5 (Python package) examples",
        "url": "https://github.com/p5py/p5",
        "branch": "master",
        "paths": ["docs/examples"],
        "licence": "GPL-3.0 (LICENSE)",
    },
    {
        "name": "pygame-ce examples",
        "url": "https://github.com/pygame-community/pygame-ce",
        "branch": "main",
        "paths": ["examples"],
        "licence": "Public domain (README.rst: \"the programs in the examples subdirectory\")",
    },
    {
        "name": "Nature of Code examples (Processing)",
        "url": "https://github.com/nature-of-code/noc-examples-processing",
        "branch": "master",
        "paths": ["."],
        "licence": "MIT (repository LICENSE)",
    },
    {
        "name": "Nature of Code examples (p5.js)",
        "url": "https://github.com/nature-of-code/noc-examples-p5.js-archived",
        "branch": "master",
        "paths": ["."],
        "licence": "MIT (repository LICENSE)",
    },
]


def fetch_corpora(out_dir: Path) -> None:
    """Shallow, sparse-checkout clone every corpus in CORPORA into out_dir.

    Records name, url, branch, commit hash and paths compared in out_dir/corpora.json.
    The only part of this tool that touches the network.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    recorded = []
    for corpus in CORPORA:
        dest = out_dir / corpus["name"].split(" ")[0].strip("()").lower().replace(".", "")
        # Use a clean, filesystem-safe folder name derived from the repo, not the description.
        dest = out_dir / Path(corpus["url"]).name
        print(f"fetching {corpus['name']} -> {dest}")
        if dest.exists():
            print(f"  already present, skipping clone")
        else:
            try:
                whole_repo = corpus["paths"] == ["."]
                clone_cmd = ["git", "clone", "--depth", "1", "--filter=blob:none"]
                if not whole_repo:
                    clone_cmd.append("--sparse")
                clone_cmd += ["--branch", corpus["branch"], corpus["url"], str(dest)]
                subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
                if not whole_repo:
                    subprocess.run(
                        ["git", "sparse-checkout", "set", *corpus["paths"]],
                        cwd=dest, check=True, capture_output=True, text=True,
                    )
            except subprocess.CalledProcessError as exc:
                print(f"  FAILED: {exc.stderr.strip()}")
                continue
        try:
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=dest, check=True,
                capture_output=True, text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            commit = "unknown"
        recorded.append({
            "name": corpus["name"],
            "url": corpus["url"],
            "branch": corpus["branch"],
            "commit": commit,
            "paths": corpus["paths"],
            "licence": corpus["licence"],
            "folder": dest.name,
        })
    (out_dir / "corpora.json").write_text(json.dumps(recorded, indent=2), encoding="utf-8")
    print(f"wrote {out_dir / 'corpora.json'}")


# ---------------------------------------------------------------------------
# Code units: a piece of code with a label, drawn either from a whole file or
# from a fenced/indented block found inside a markup file.
# ---------------------------------------------------------------------------

@dataclass
class CodeUnit:
    label: str
    text: str


CODE_EXTS = {".py", ".pyde", ".js", ".mjs", ".ts", ".pde", ".java"}

FENCE_RE = re.compile(r"```([\w+-]*)[ \t]*\n(.*?)\n```", re.S)
INDENT_RE = re.compile(r"(?:^(?:[ \t]{4,}\S.*)\n?){2,}", re.M)
SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S | re.I)
CODE_TAG_RE = re.compile(r"<code\b[^>]*>(.*?)</code>", re.S | re.I)
RST_BLOCK_RE = re.compile(
    r"(?:^\.\.[ \t]+[\w-]+::[^\n]*|::)\n\n((?:[ \t]+.*\n?)+)", re.M
)
YAML_BLOCK_RE = re.compile(r"^[ \t]*[\w.-]+:\s*[|>][+-]?\s*\n((?:[ \t]+.*\n?)+)", re.M)
# p5.js documents each function with a JSDoc block containing one or more small
# @example sections (see src/color/creating_reading.js). Splitting on @example, rather
# than treating the whole source file as one unit, keeps each comparison to the size of
# one real sketch instead of a file-long soup of hundreds of tiny examples concatenated
# together, which otherwise produces long "common runs" of the shared reference-example
# idiom (createCanvas/background/fill/rect/describe) purely by chance.
JSDOC_EXAMPLE_RE = re.compile(r"@example\b[ \t]*\r?\n((?:[ \t]*\*(?!/)(?!\s*@)[^\n]*\r?\n)+)")

MIN_BLOCK_CHARS = 20


def extract_markdown_blocks(text: str) -> list[tuple[str, str]]:
    """Fenced ```lang blocks, then indented blocks in whatever text is left over."""
    blocks: list[tuple[str, str]] = []
    remainder = []
    last_end = 0
    for i, m in enumerate(FENCE_RE.finditer(text), start=1):
        lang = (m.group(1) or "text").lower()
        blocks.append((f"fence{i}({lang})", m.group(2)))
        remainder.append(text[last_end:m.start()])
        last_end = m.end()
    remainder.append(text[last_end:])
    leftover = "\n".join(remainder)
    for j, m in enumerate(INDENT_RE.finditer(leftover), start=1):
        blocks.append((f"indent{j}", m.group(0)))
    return [(name, code) for name, code in blocks if len(code.strip()) >= MIN_BLOCK_CHARS]


def extract_html_blocks(text: str) -> list[tuple[str, str]]:
    blocks = []
    for i, m in enumerate(SCRIPT_RE.finditer(text), start=1):
        blocks.append((f"script{i}", m.group(1)))
    for j, m in enumerate(CODE_TAG_RE.finditer(text), start=1):
        blocks.append((f"code{j}", m.group(1)))
    return [(name, code) for name, code in blocks if len(code.strip()) >= MIN_BLOCK_CHARS]


def extract_rst_blocks(text: str) -> list[tuple[str, str]]:
    blocks = []
    for i, m in enumerate(RST_BLOCK_RE.finditer(text), start=1):
        blocks.append((f"rst{i}", m.group(1)))
    return [(name, code) for name, code in blocks if len(code.strip()) >= MIN_BLOCK_CHARS]


def extract_yaml_blocks(text: str) -> list[tuple[str, str]]:
    blocks = []
    for i, m in enumerate(YAML_BLOCK_RE.finditer(text), start=1):
        blocks.append((f"yaml{i}", m.group(1)))
    return [(name, code) for name, code in blocks if len(code.strip()) >= MIN_BLOCK_CHARS]


def extract_jsdoc_examples(text: str) -> list[tuple[str, str]]:
    """Each @example section in a JSDoc comment, as its own small block of code."""
    blocks = []
    for i, m in enumerate(JSDOC_EXAMPLE_RE.finditer(text), start=1):
        lines = []
        for line in m.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith("*"):
                stripped = stripped[1:]
            if stripped.startswith(" "):
                stripped = stripped[1:]
            lines.append(stripped)
        blocks.append((f"example{i}", "\n".join(lines)))
    return [(name, code) for name, code in blocks if len(code.strip()) >= MIN_BLOCK_CHARS]


MARKUP_EXTRACTORS = {
    ".md": extract_markdown_blocks,
    ".mdx": extract_markdown_blocks,
    ".html": extract_html_blocks,
    ".htm": extract_html_blocks,
    ".rst": extract_rst_blocks,
    ".yaml": extract_yaml_blocks,
    ".yml": extract_yaml_blocks,
}


def units_from_file(path: Path, root_for_label: Path) -> list[CodeUnit]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    label_base = str(path.relative_to(root_for_label)) if _is_relative_to(path, root_for_label) else str(path)
    ext = path.suffix.lower()
    if ext in (".js", ".mjs", ".ts"):
        jsdoc_blocks = extract_jsdoc_examples(text)
        if jsdoc_blocks:
            return [CodeUnit(label=f"{label_base}#{name}", text=code) for name, code in jsdoc_blocks]
        return [CodeUnit(label=label_base, text=text)]
    if ext in CODE_EXTS:
        return [CodeUnit(label=label_base, text=text)]
    extractor = MARKUP_EXTRACTORS.get(ext)
    if extractor:
        return [CodeUnit(label=f"{label_base}#{name}", text=code) for name, code in extractor(text)]
    return []


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}


def iter_corpus_units(corpus_dir: Path) -> list[CodeUnit]:
    units: list[CodeUnit] = []
    for path in sorted(corpus_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        units.extend(units_from_file(path, corpus_dir))
    return units


def default_our_units(root: Path = ROOT) -> list[CodeUnit]:
    units: list[CodeUnit] = []
    for path in sorted((root / "examples").rglob("*.py")):
        units.append(CodeUnit(label=str(path.relative_to(root)).replace("\\", "/"),
                               text=path.read_text(encoding="utf-8")))
    for path in sorted((root / "docs" / "guide").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for name, code in extract_markdown_blocks(text):
            lang = name.split("(")[-1].rstrip(")")
            if lang in ("python", "py"):
                label = f"{path.relative_to(root)}#{name}".replace("\\", "/")
                units.append(CodeUnit(label=label, text=code))
    return units


def units_from_paths(paths: list[str], root: Path = ROOT) -> list[CodeUnit]:
    units: list[CodeUnit] = []
    for p in paths:
        path = Path(p)
        if path.suffix == ".py":
            units.append(CodeUnit(label=str(path), text=path.read_text(encoding="utf-8")))
        elif path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            for name, code in extract_markdown_blocks(text):
                lang = name.split("(")[-1].rstrip(")")
                if lang in ("python", "py"):
                    units.append(CodeUnit(label=f"{path}#{name}", text=code))
    return units


# ---------------------------------------------------------------------------
# Fingerprints
# ---------------------------------------------------------------------------

CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def to_snake_case(name: str) -> str:
    return CAMEL_RE.sub("_", name).lower()


# Keywords across Python / JS / Java that can precede "(" without being a call.
NOT_CALLS = {
    "if", "for", "while", "switch", "catch", "function", "def", "class", "elif",
    "except", "with", "else", "do", "return", "new", "typeof", "instanceof",
    "var", "let", "const", "import", "from", "async", "await", "yield", "try",
    "finally", "case", "super", "this", "in", "and", "or", "not", "lambda",
    "print",  # too generic a builtin to be a useful signal either way
}

CALL_RE = re.compile(r"(?:[A-Za-z_$][\w$]*\.)?([A-Za-z_$][\w$]*)\s*\(")


def extract_calls(text: str) -> list[str]:
    calls = []
    for m in CALL_RE.finditer(text):
        name = m.group(1)
        if name in NOT_CALLS:
            continue
        calls.append(to_snake_case(name))
    return calls


COMMON_SIZES = {
    80, 100, 120, 160, 200, 240, 300, 320, 360, 400, 480, 500, 600,
    640, 700, 720, 768, 800, 900, 1000, 1024, 1080, 1280, 1920,
}
IGNORED_NUMBERS = {"0", "1", "2"}

NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")


def extract_numbers(text: str) -> list[str]:
    """Numeric literals from the code itself, not from comments or strings.

    A comment that restates a nearby literal ("# centre at (140, 140)") would otherwise
    echo the same value straight back into the sequence next to itself, manufacturing a
    short run of identical digits that says nothing about where the number came from.
    """
    excluded = [(m.start(), m.end()) for m in COMMENT_STRING_RE.finditer(text)]
    numbers = []
    for m in NUMBER_RE.finditer(text):
        start = m.start()
        if any(s <= start < e for s, e in excluded):
            continue
        raw = m.group(0)
        value = float(raw)
        if value in (0, 1, 2) or (value == int(value) and int(value) in COMMON_SIZES):
            continue
        # Normalise "40" and "40.0" to the same token.
        numbers.append(str(value) if "." in raw else raw)
    return numbers


COMMENT_STRING_RE = re.compile(
    r"\"\"\"(.*?)\"\"\""       # python triple double
    r"|'''(.*?)'''"            # python triple single
    r"|#[^\n]*"                # python comment
    r"|//[^\n]*"               # js/java line comment
    r"|/\*.*?\*/"              # js/java block comment
    r"|\"(?:[^\"\\\n]|\\.)*\"" # double-quoted string
    r"|'(?:[^'\\\n]|\\.)*'"    # single-quoted string
    r"|`(?:[^`\\]|\\.)*`",     # JS template string
    re.S,
)
WORD_RE = re.compile(r"[A-Za-z']+")


def extract_words(text: str) -> list[str]:
    words = []
    for m in COMMENT_STRING_RE.finditer(text):
        chunk = m.group(0)
        words.extend(w.lower() for w in WORD_RE.findall(chunk))
    return words


# Identifiers that are part of the craft's shared vocabulary, not a "written expression".
COMMON_IDENTIFIERS = {
    "x", "y", "z", "i", "j", "k", "n", "w", "h", "r", "g", "b", "a", "dx", "dy",
    "setup", "draw", "width", "height", "size", "background", "fill", "stroke",
    "circle", "rect", "square", "ellipse", "triangle", "quad", "line", "point",
    "color", "colour", "position", "pos", "velocity", "vel", "vector", "mover",
    "gravity", "wind", "speed", "frame", "count", "random", "noise", "seed",
    "angle", "radius", "diameter", "self", "this", "true", "false", "none",
    "null", "import", "def", "function", "var", "let", "const", "return",
    "global", "main", "run", "args", "kwargs", "min", "max", "map", "lerp",
    "constrain", "print", "console", "log", "new", "class", "public", "static",
    "void", "int", "float", "double", "string", "boolean", "float_", "num",
    "value", "val", "index", "idx", "item", "items", "list", "array", "def_",
}
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def extract_identifiers(text: str) -> set[str]:
    names = set()
    for m in IDENTIFIER_RE.finditer(text):
        name = m.group(0)
        start, end = m.span()
        # Skip call sites (name immediately followed by "(") and attribute access
        # (name immediately preceded by "."): both are API surface, not a variable.
        after = text[end:end + 1]
        before = text[start - 1:start]
        if after == "(" or before == ".":
            continue
        normalised = to_snake_case(name)
        if len(normalised) <= 2 or normalised in COMMON_IDENTIFIERS or normalised in NOT_CALLS:
            continue
        names.add(normalised)
    return names


@dataclass
class Fingerprint:
    calls: list[str] = field(default_factory=list)
    numbers: list[str] = field(default_factory=list)
    words: list[str] = field(default_factory=list)
    identifiers: set[str] = field(default_factory=set)

    @classmethod
    def of(cls, text: str) -> "Fingerprint":
        return cls(
            calls=extract_calls(text),
            numbers=extract_numbers(text),
            words=extract_words(text),
            identifiers=extract_identifiers(text),
        )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def ngrams(seq: list[str], n: int) -> list[tuple]:
    if len(seq) < n:
        return []
    return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]


def containment(a: list[str], b: list[str], n: int) -> float:
    a_grams = set(ngrams(a, n))
    if not a_grams:
        return 0.0
    b_grams = set(ngrams(b, n))
    return len(a_grams & b_grams) / len(a_grams)


def longest_common_run(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


@dataclass
class Comparison:
    calls_containment: float
    calls_run: int
    numbers_containment: float
    words_run: int
    identifiers_jaccard: float
    combined: float

    @property
    def word_score(self) -> float:
        return min(1.0, self.words_run / 8)


def compare(ours: Fingerprint, theirs: Fingerprint) -> Comparison:
    calls_containment = containment(ours.calls, theirs.calls, 5)
    calls_run = longest_common_run(ours.calls, theirs.calls)
    numbers_containment = containment(ours.numbers, theirs.numbers, 4)
    words_run = longest_common_run(ours.words, theirs.words)
    id_jaccard = jaccard(ours.identifiers, theirs.identifiers)

    # Creative-coding sketches share a small, well-worn vocabulary of call names
    # (background, fill, circle, ...), so on a large corpus a run of six or more
    # matching calls turns up by chance alone -- it is not, by itself, evidence of
    # copying. Numbers and wording are the reliable signals: unrelated sketches
    # essentially never share a run of magic numbers or eight words in a row, so the
    # combined score leans on them, and calls only corroborate rather than decide.
    word_score = min(1.0, words_run / 8)
    combined = 0.25 * calls_containment + 0.30 * numbers_containment + 0.30 * word_score + 0.15 * id_jaccard

    return Comparison(
        calls_containment=calls_containment,
        calls_run=calls_run,
        numbers_containment=numbers_containment,
        words_run=words_run,
        identifiers_jaccard=id_jaccard,
        combined=combined,
    )


# A pair is flagged when the combined score is high, or when one signal is strong
# enough on its own to be convincing regardless of the others (a faithful translation
# keeps its calls and numbers even after every name and comment is changed). Calls
# alone, however strong, never flag a pair on their own: see the note in compare().
COMBINED_THRESHOLD = 0.55
STRONG_CALL_AND_NUMBER = (0.6, 0.5)     # (calls_containment, numbers_containment)
STRONG_NUMBER_AND_RUN = (0.75, 5)       # (numbers_containment, calls_run)
STRONG_WORD_RUN = 8


def is_flagged(c: Comparison) -> bool:
    return (
        c.combined >= COMBINED_THRESHOLD
        or (c.calls_containment >= STRONG_CALL_AND_NUMBER[0] and c.numbers_containment >= STRONG_CALL_AND_NUMBER[1])
        or (c.numbers_containment >= STRONG_NUMBER_AND_RUN[0] and c.calls_run >= STRONG_NUMBER_AND_RUN[1])
        or c.words_run >= STRONG_WORD_RUN
    )


@dataclass
class Result:
    our_label: str
    best_label: str | None
    comparison: Comparison | None
    flagged: bool


def compare_all(our_units: list[CodeUnit], corpus_units: list[CodeUnit]) -> list[Result]:
    corpus_fps = [(u.label, Fingerprint.of(u.text)) for u in corpus_units]
    results = []
    for unit in our_units:
        ours_fp = Fingerprint.of(unit.text)
        best_label = None
        best_comparison = None
        for label, theirs_fp in corpus_fps:
            c = compare(ours_fp, theirs_fp)
            if best_comparison is None or c.combined > best_comparison.combined:
                best_label, best_comparison = label, c
        flagged = bool(best_comparison and is_flagged(best_comparison))
        results.append(Result(unit.label, best_label, best_comparison, flagged))
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_table(results: list[Result]) -> str:
    header = ("our example", "closest corpus file", "calls", "numbers", "words", "identifiers", "combined", "flagged")
    rows = [header]
    for r in results:
        if r.comparison is None:
            rows.append((r.our_label, "(no corpus files)", "-", "-", "-", "-", "-", "no"))
            continue
        c = r.comparison
        rows.append((
            r.our_label, r.best_label,
            f"{c.calls_containment:.2f}", f"{c.numbers_containment:.2f}",
            f"{c.words_run}", f"{c.identifiers_jaccard:.2f}",
            f"{c.combined:.2f}", "YES" if r.flagged else "no",
        ))
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(header))]
    lines = []
    for row in rows:
        lines.append(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)


def format_markdown(results: list[Result]) -> str:
    header = ("our example", "closest corpus file", "calls", "numbers", "words run", "identifiers", "combined", "flagged")
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in results:
        if r.comparison is None:
            lines.append(f"| {r.our_label} | (no corpus files) | - | - | - | - | - | no |")
            continue
        c = r.comparison
        lines.append(
            f"| {r.our_label} | {r.best_label} | {c.calls_containment:.2f} | "
            f"{c.numbers_containment:.2f} | {c.words_run} | {c.identifiers_jaccard:.2f} | "
            f"{c.combined:.2f} | {'YES' if r.flagged else 'no'} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", action="append", default=[], help="directory of corpus files (repeatable)")
    parser.add_argument("--report", help="write the results table as Markdown to this file")
    parser.add_argument("--fetch", help="clone the pinned corpora into this directory and exit")
    parser.add_argument("paths", nargs="*", help="our files to check (default: all example code)")
    args = parser.parse_args(argv)

    if args.fetch:
        fetch_corpora(Path(args.fetch))
        return 0

    our_units = units_from_paths(args.paths) if args.paths else default_our_units()
    corpus_units: list[CodeUnit] = []
    for corpus_dir in args.corpus:
        corpus_units.extend(iter_corpus_units(Path(corpus_dir)))

    if not corpus_units:
        print("no corpus files found; pass --corpus DIR (see --fetch to build one)", file=sys.stderr)
        return 2

    results = compare_all(our_units, corpus_units)
    print(f"{len(our_units)} of our examples compared with {len(corpus_units)} corpus files")
    print(format_table(results))

    if args.report:
        Path(args.report).write_text(format_markdown(results), encoding="utf-8")
        print(f"report -> {args.report}")

    flagged = [r for r in results if r.flagged]
    if flagged:
        print(f"\n{len(flagged)} pair(s) flagged.")
        return 1
    print("\nnothing flagged.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
