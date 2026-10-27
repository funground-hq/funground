"""Fonts from the web (S-230, D-119, contract T11): an address where a path goes, a copy kept in `fonts/`, and a
provider that finds a family by name.

    f.load_font("https://.../Lora%5Bwght%5D.ttf")
        -> <sketch folder>/fonts/Lora[wght].ttf          the copy, kept the first time
        -> <sketch folder>/fonts/sources.json            {"Lora[wght].ttf": "https://.../Lora%5Bwght%5D.ttf"}

A second run finds the file and the index entry and never asks the network. This module is the only code in
funground that reads the network. It uses the standard library's urllib; a host that cannot (the browser) installs
its own fetcher with `set_url_fetcher()`. It does not import `typography`: the caller passes a `check` function that
refuses bytes that are not a font, so the two modules do not need each other.
"""
from __future__ import annotations

import json
import os
import re
import socket
from collections.abc import Callable
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

MAX_BYTES = 30 * 1024 * 1024          # a font bigger than this is refused
TIMEOUT = 20.0                        # seconds to wait for the site
FONTS_FOLDER = "fonts"
INDEX_NAME = "sources.json"
GOOGLE_FONTS = "google_fonts"         # the word of f.CONSTANTS.PROVIDERS.GOOGLE_FONTS
PROVIDER_WORDS = (GOOGLE_FONTS,)
GOOGLE_RAW = "https://raw.githubusercontent.com/google/fonts/main"
GOOGLE_LICENCES = ("ofl", "apache", "ufl")      # the folders of google/fonts, in the order they are tried

# The browser (S-230): the host installs `fetcher(address) -> bytes`; its failures are already ConnectionError.
_url_fetcher: Callable[[str], bytes] | None = None
_memory: dict[tuple, object] = {}     # what was found in this process, so a text_font() in draw() reads no files


def set_url_fetcher(fetcher: Callable[[str], bytes] | None) -> None:
    """Install (or, with None, remove) the function that downloads an address instead of urllib."""
    global _url_fetcher
    _url_fetcher = fetcher


def forget() -> None:
    """Forget what this process found (the next load looks at the files again)."""
    _memory.clear()


# ---- addresses
def is_address(text: object) -> bool:
    """True for a string that starts with http:// or https://."""
    return isinstance(text, str) and text.lower().startswith(("http://", "https://"))


_GITHUB_FILE = re.compile(r"^https?://(?:www\.)?github\.com/([^/?#]+)/([^/?#]+)/(?:blob|raw)/([^?#]+)", re.IGNORECASE)


def raw_address(address: str) -> str:
    """A github.com file address (`/blob/` or `/raw/`) as the raw.githubusercontent.com address of the same file.
    github.com answers a browser with a redirect that the browser refuses; the raw host serves the file itself.
    Any other address is returned as it is."""
    match = _GITHUB_FILE.match(address.strip())
    if match is None:
        return address.strip()
    owner, repo, rest = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{rest}"


_BAD_NAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def file_name_of(address: str) -> str:
    """The name the copy is kept under: the address's last part, URL-decoded ("Lora%5Bwght%5D.ttf" -> "Lora[wght].ttf")."""
    last = unquote(urlparse(address).path.rsplit("/", 1)[-1])
    last = _BAD_NAME_CHARS.sub("_", last).strip(" .")
    return last or "font.ttf"


# ---- the network
def _short(reason: object) -> str:
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "timed out"
    text = str(reason).strip() or type(reason).__name__
    return text[:80]


def _download_urllib(address: str) -> bytes:
    from . import __version__

    who = "f.load_font()"
    request = Request(address, headers={"User-Agent": f"funground/{__version__}"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            data = response.read(MAX_BYTES + 1)
    except HTTPError as error:
        if error.code == 404:
            raise FileNotFoundError(f"{who}: there is no font at '{address}' (the site answered 404).") from None
        raise ConnectionError(f"{who}: could not download '{address}' (the site answered {error.code}).") from None
    except URLError as error:
        raise ConnectionError(_offline(address, _short(error.reason))) from None
    except (OSError, HTTPException, ValueError) as error:          # a timeout while reading, a dropped line, a bad address
        raise ConnectionError(_offline(address, _short(error))) from None
    return data


def _offline(address: str, reason: str) -> str:
    return (f"f.load_font(): could not download '{address}' ({reason}). Run the sketch once while online; "
            "after that funground uses the copy in fonts/.")


def download(address: str) -> bytes:
    """The bytes at *address*. Raises ConnectionError (no connection, timeout, or a host that refused),
    FileNotFoundError (404) or ValueError (more than 30 MB)."""
    data = _url_fetcher(address) if _url_fetcher is not None else _download_urllib(address)
    if len(data) > MAX_BYTES:
        raise ValueError(f"f.load_font(): '{address}' is larger than {MAX_BYTES // (1024 * 1024)} MB, which is too big for a font.")
    return data


# ---- the copy in fonts/
def _folder(base_dir: str | None) -> str:
    return os.path.join(base_dir if base_dir is not None else os.getcwd(), FONTS_FOLDER)


def _read_index(folder: str) -> dict[str, str]:
    try:
        with open(os.path.join(folder, INDEX_NAME), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def _write_index(folder: str, index: dict[str, str]) -> None:
    target = os.path.join(folder, INDEX_NAME)
    temporary = target + ".part"
    with open(temporary, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(index, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    os.replace(temporary, target)


def _candidates(name: str):
    """name, then name~2, name~3, ... (the number goes before the ending: Lora~2.ttf)."""
    yield name
    stem, ending = os.path.splitext(name)
    n = 2
    while True:
        yield f"{stem}~{n}{ending}"
        n += 1


def kept(address: str, base_dir: str | None, name: str | None = None) -> str | None:
    """The kept copy of *address* in fonts/, or None. Reads no network."""
    folder = _folder(base_dir)
    index = _read_index(folder)
    for candidate in _candidates(name or file_name_of(address)):
        path = os.path.join(folder, candidate)
        if not os.path.exists(path):
            return None
        if index.get(candidate) == address:
            return path
    return None  # pragma: no cover  (the loop only ends at a free name)


def keep_copy(address: str, base_dir: str | None, check: Callable[[str], None], name: str | None = None) -> str:
    """The path of the kept copy of *address* in fonts/ beside the sketch: the copy that is there already, or a
    download. *check(path)* is given the downloaded file under a temporary name and raises ValueError when it is not
    what was wanted, so a bad download is never kept. *name* is the file name to keep it under (default: the
    address's own)."""
    path = kept(address, base_dir, name)
    if path is not None:
        return path
    data = download(address)
    folder = _folder(base_dir)
    os.makedirs(folder, exist_ok=True)
    index = _read_index(folder)
    final = next(c for c in _candidates(name or file_name_of(address)) if not os.path.exists(os.path.join(folder, c)))
    temporary = os.path.join(folder, final + ".part")
    try:
        with open(temporary, "wb") as fh:
            fh.write(data)
        check(temporary)
        os.replace(temporary, os.path.join(folder, final))
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
    index[final] = address
    _write_index(folder, index)
    return os.path.join(folder, final)


def font_path(address: str, base_dir: str | None, check: Callable[[str], None]) -> str:
    """The kept copy of the font at *address* (a github.com address is read from raw.githubusercontent.com)."""
    address = raw_address(address)
    key = ("address", _folder(base_dir), address)
    path = _memory.get(key)
    if path is None or not os.path.exists(path):
        path = _memory[key] = keep_copy(address, base_dir, check)
    return path


def sources_of(paths) -> dict[str, str]:
    """For `f.keep()`: {file name: address} for those of *paths* that are kept web fonts (listed in a sources.json
    beside them)."""
    found: dict[str, str] = {}
    for path in paths:
        folder, name = os.path.split(path)
        address = _read_index(folder).get(name)
        if address is not None and os.path.basename(folder) == FONTS_FOLDER:
            found[name] = address
    return dict(sorted(found.items()))


# ---- a provider finds a family by name
def check_provider(provider: object) -> str:
    """The provider word, or ValueError / TypeError that lists the words."""
    if not isinstance(provider, str):
        raise TypeError(f"f.load_font(): provider is a word such as f.CONSTANTS.PROVIDERS.GOOGLE_FONTS, not {type(provider).__name__}")
    if provider not in PROVIDER_WORDS:
        raise ValueError(f"f.load_font(): provider must be one of {', '.join(repr(w) for w in PROVIDER_WORDS)} "
                         f"(f.CONSTANTS.PROVIDERS.GOOGLE_FONTS), not {provider!r}")
    return provider


def parse_metadata(text: str) -> tuple[list[dict], dict[str, tuple[float, float]]]:
    """Read a family's `METADATA.pb` from google/fonts: its `fonts { ... }` blocks (style, weight, filename) and
    its `axes { ... }` blocks (tag -> (min_value, max_value)). A small reader of the text format; other
    fields and nested blocks are skipped."""
    fonts: list[dict] = []
    axes: dict[str, tuple[float, float]] = {}
    depth, block, fields = 0, "", {}
    for raw in text.splitlines():
        line = raw.strip()
        pair = re.match(r"^(\w+)\s*:\s*(.*)$", line)
        if pair is not None:
            if depth == 1 and block in ("fonts", "axes"):
                value = pair.group(2).strip()
                fields[pair.group(1)] = value[1:-1] if value.startswith('"') and value.endswith('"') and len(value) >= 2 else value
            continue
        opened = re.match(r"^(\w+)\s*\{$", line)
        if opened is not None:
            depth += 1
            if depth == 1:
                block, fields = opened.group(1), {}
        elif line.startswith("}"):
            if depth == 1 and block == "fonts" and fields.get("filename"):
                try:
                    weight = float(fields.get("weight", "400"))
                except ValueError:
                    weight = 400.0
                fonts.append({"style": fields.get("style", "normal"), "weight": weight, "filename": fields["filename"]})
            elif depth == 1 and block == "axes" and "tag" in fields:
                try:
                    axes[fields["tag"]] = (float(fields["min_value"]), float(fields["max_value"]))
                except (KeyError, ValueError):
                    pass
            depth = max(0, depth - 1)
    return fonts, axes


def choose_file(fonts: list[dict], axes: dict[str, tuple[float, float]], weight: float | None,
                italic: bool) -> tuple[str, float | None] | None:
    """Pick one file of a family: (file name, wght to set by default or None), or None when no file has the style.

    The file must have the style. Then a static file of exactly the weight wins; else a variable file whose wght
    axis covers the weight; else the file nearest in weight. Without a weight, 400 is wanted and nothing is set."""
    style = "italic" if italic else "normal"
    same = [f for f in fonts if f["style"] == style]
    if not same:
        return None
    want = 400.0 if weight is None else float(weight)
    wght = axes.get("wght")

    def variable(entry: dict) -> bool:
        return wght is not None and "[" in entry["filename"]

    def setting(entry: dict) -> float | None:
        if weight is None or not variable(entry):
            return None
        return min(max(want, wght[0]), wght[1])

    for entry in same:
        if not variable(entry) and entry["weight"] == want:
            return entry["filename"], None
    for entry in same:
        if variable(entry) and wght[0] <= want <= wght[1]:
            return entry["filename"], setting(entry)

    def distance(entry: dict) -> float:
        if variable(entry):
            return max(wght[0] - want, want - wght[1], 0.0)
        return abs(entry["weight"] - want)

    best = min(same, key=distance)
    return best["filename"], setting(best)


def family_directory(family: str) -> str:
    """The folder of a family in google/fonts: lower case, without spaces and hyphens."""
    return re.sub(r"[\s\-]+", "", family.lower())


def _check_metadata(path: str) -> None:
    with open(path, encoding="utf-8", errors="replace") as fh:
        fonts, _ = parse_metadata(fh.read())
    if not fonts:
        raise ValueError("not a METADATA.pb file")


def google_font(family: str, weight: float | None, italic: bool, base_dir: str | None) -> tuple[str, float | None]:
    """The address of the file of a Google Fonts family that fits *weight* and *italic*, and the wght to set by
    default (None for a static font, or when no weight was asked for). Reads the family's METADATA.pb
    (the copy in fonts/ when there is one) from the google/fonts repository."""
    who = "f.load_font()"
    key = ("google", _folder(base_dir), family, weight, italic)
    found = _memory.get(key)
    if found is not None and os.path.exists(found[2]):
        return found[0], found[1]
    directory = family_directory(family)
    name = _BAD_NAME_CHARS.sub("_", f"{directory}.METADATA.pb")
    folder_word = quote(directory, safe="")
    addresses = [f"{GOOGLE_RAW}/{licence}/{folder_word}/METADATA.pb" for licence in GOOGLE_LICENCES]
    metadata_path = metadata_address = None
    for candidate in addresses:                                  # a copy kept before: no network
        metadata_path = kept(candidate, base_dir, name)
        if metadata_path is not None:
            metadata_address = candidate
            break
    if metadata_path is None and directory:
        for candidate in addresses:
            try:
                metadata_path = keep_copy(candidate, base_dir, _check_metadata, name)
            except FileNotFoundError:
                continue
            metadata_address = candidate
            break
    if metadata_path is None:
        raise FileNotFoundError(f"{who}: Google Fonts has no family called '{family}'.")
    with open(metadata_path, encoding="utf-8", errors="replace") as fh:
        fonts, axes = parse_metadata(fh.read())
    chosen = choose_file(fonts, axes, weight, italic)
    if chosen is None:
        raise FileNotFoundError(f"{who}: the Google Fonts family '{family}' has no {'italic' if italic else 'upright'} font.")
    address = metadata_address.rsplit("/", 1)[0] + "/" + quote(chosen[0])
    _memory[key] = (address, chosen[1], metadata_path)
    return address, chosen[1]
