"""Fonts from the web (S-230, D-119, contract T11): an address where a path goes, the copy kept in fonts/, a provider
that finds a family by name, WOFF read and WOFF2 refused, and the host's own fetcher.

A local HTTP server in a thread stands in for the internet. Only the last test uses the real network, and it skips
when there is none. Test fonts come from tests/fontmaker.py.
"""
from __future__ import annotations

import io
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

import pytest
from fontTools.ttLib import TTFont

import funground as f
from funground import api, typography, web_fonts
from funground.web import Session

from conftest import ROOT
from fontmaker import make_static_font, make_variable_font

WOFF2_MESSAGE = ("f.load_font(): 'x.woff2' is a WOFF2 file, which funground cannot read. "
                 "Use the .ttf version of the font; most font sites offer it.")


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    """Each test gets its own font registry and memory, a short timeout and no host fetcher."""
    saved_registry, saved_paths = dict(typography._registry), dict(typography._path_to_key)
    typography._registry.clear()
    typography._path_to_key.clear()
    typography.files_read.clear()
    web_fonts.forget()
    web_fonts.set_url_fetcher(None)
    monkeypatch.setattr(web_fonts, "TIMEOUT", 0.5)
    yield
    web_fonts.set_url_fetcher(None)
    web_fonts.forget()
    typography.files_read.clear()
    typography._registry.clear()
    typography._registry.update(saved_registry)
    typography._path_to_key.clear()
    typography._path_to_key.update(saved_paths)


class Server:
    """A web server on this computer. `routes` maps a path to (status, bytes); a path in `slow` waits."""

    def __init__(self) -> None:
        self.routes: dict[str, tuple[int, bytes]] = {}
        self.slow: set[str] = set()
        self.hits: list[str] = []
        self.agents: list[str] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = unquote(self.path)
                outer.hits.append(path)
                outer.agents.append(self.headers.get("User-Agent", ""))
                if path in outer.slow:
                    time.sleep(2)
                status, body = outer.routes.get(path, (404, b"not found"))
                try:
                    self.send_response(status)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except OSError:
                    pass

            def log_message(self, *args):
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def server():
    s = Server()
    yield s
    try:
        s.stop()
    except Exception:
        pass


@pytest.fixture
def fonts(tmp_path):
    """TTF, WOFF and WOFF2-magic bytes of the same small font, and a variable font."""
    folder = tmp_path / "made"
    folder.mkdir()
    ttf = Path(make_static_font(folder))
    font = TTFont(str(ttf))
    font.flavor = "woff"
    buffer = io.BytesIO()
    font.save(buffer)
    return {"ttf": ttf.read_bytes(), "woff": buffer.getvalue(), "woff2": b"wOF2" + b"\0" * 60,
            "variable": Path(make_variable_font(folder)).read_bytes(), "ttf_path": ttf}


def sketch_folder(tmp_path) -> str:
    folder = tmp_path / "sketch"
    folder.mkdir(exist_ok=True)
    return str(folder)


def load(address, tmp_path, **options):
    return typography.load_font(address, sketch_folder(tmp_path), **options)


def forget_loaded():
    typography._registry.clear()
    typography._path_to_key.clear()
    web_fonts.forget()


# ---------------------------------------------------------------- addresses
@pytest.mark.parametrize("given, wanted", [
    ("https://github.com/google/fonts/blob/main/ofl/lora/Lora%5Bwght%5D.ttf",
     "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora%5Bwght%5D.ttf"),
    ("https://github.com/google/fonts/raw/main/ofl/lora/Lora[wght].ttf",
     "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora[wght].ttf"),
    ("http://www.github.com/me/repo/blob/v1.2/fonts/A.ttf?raw=true",
     "https://raw.githubusercontent.com/me/repo/v1.2/fonts/A.ttf"),
    ("https://raw.githubusercontent.com/google/fonts/main/ofl/lora/OFL.txt",
     "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/OFL.txt"),
    ("https://example.com/github.com/a/b/blob/c/d.ttf", "https://example.com/github.com/a/b/blob/c/d.ttf"),
    ("https://github.com/google/fonts", "https://github.com/google/fonts"),
])
def test_a_github_address_is_read_from_the_raw_host(given, wanted):
    assert web_fonts.raw_address(given) == wanted


def test_an_address_is_a_string_that_starts_with_http_or_https():
    assert web_fonts.is_address("https://a.b/c.ttf") and web_fonts.is_address("http://a.b/c.ttf")
    assert not web_fonts.is_address("fonts/https.ttf") and not web_fonts.is_address(None)


def test_the_file_name_is_the_last_part_decoded():
    assert web_fonts.file_name_of("https://x.org/a/Lora%5Bwght%5D.ttf") == "Lora[wght].ttf"
    assert web_fonts.file_name_of("https://x.org/a/b.ttf?v=2#top") == "b.ttf"
    assert web_fonts.file_name_of("https://x.org/") == "font.ttf"
    assert "/" not in web_fonts.file_name_of("https://x.org/a/..%2F..%2Fevil.ttf")


# ---------------------------------------------------------------- the download and the kept copy
def test_an_address_is_downloaded_and_a_copy_is_kept(tmp_path, server, fonts):
    server.routes["/a/Test.ttf"] = (200, fonts["ttf"])
    font = load(server.url("/a/Test.ttf"), tmp_path)
    kept = Path(tmp_path / "sketch" / "fonts" / "Test.ttf")
    assert kept.read_bytes() == fonts["ttf"]
    assert font.name == "Test.ttf" and font.family() == "TestStatic"
    assert sorted(p.name for p in kept.parent.iterdir()) == ["Test.ttf", "sources.json"]      # no temporary file left
    assert server.agents == [f"funground/{f.__version__}"]


def test_a_second_run_uses_the_copy_and_never_asks_the_network(tmp_path, server, fonts):
    address = server.url("/a/Test.ttf")
    server.routes["/a/Test.ttf"] = (200, fonts["ttf"])
    load(address, tmp_path)
    server.stop()                                       # no internet any more
    forget_loaded()                                     # a new run
    again = load(address, tmp_path)
    assert again.name == "Test.ttf" and again.family() == "TestStatic"
    assert server.hits == ["/a/Test.ttf"]               # asked once, the first time only


def test_the_same_font_loaded_twice_in_a_run_is_the_same_font(tmp_path, server, fonts):
    server.routes["/Test.ttf"] = (200, fonts["ttf"])
    assert load(server.url("/Test.ttf"), tmp_path) == load(server.url("/Test.ttf"), tmp_path)
    assert len(server.hits) == 1


def test_sources_json_records_where_each_file_came_from(tmp_path, server, fonts):
    server.routes["/a/B.ttf"] = (200, fonts["ttf"])
    server.routes["/a/A%5Bwght%5D.ttf"] = (200, fonts["ttf"])
    server.routes["/a/A[wght].ttf"] = (200, fonts["ttf"])
    load(server.url("/a/B.ttf"), tmp_path)
    load(server.url("/a/A%5Bwght%5D.ttf"), tmp_path)
    text = (tmp_path / "sketch" / "fonts" / "sources.json").read_text(encoding="utf-8")
    assert text == ('{\n "A[wght].ttf": "' + server.url("/a/A%5Bwght%5D.ttf") + '",\n'
                    ' "B.ttf": "' + server.url("/a/B.ttf") + '"\n}\n')


def test_a_name_taken_by_another_address_gets_a_number(tmp_path, server, fonts):
    server.routes["/one/Same.ttf"] = (200, fonts["ttf"])
    server.routes["/two/Same.ttf"] = (200, fonts["ttf"])
    server.routes["/three/Same.ttf"] = (200, fonts["ttf"])
    first, second, third = (load(server.url(f"/{n}/Same.ttf"), tmp_path) for n in ("one", "two", "three"))
    folder = tmp_path / "sketch" / "fonts"
    assert sorted(p.name for p in folder.glob("*.ttf")) == ["Same.ttf", "Same~2.ttf", "Same~3.ttf"]
    assert [first.name, second.name, third.name] == ["Same.ttf", "Same~2.ttf", "Same~3.ttf"]
    sources = json.loads((folder / "sources.json").read_text(encoding="utf-8"))
    assert sources["Same~2.ttf"] == server.url("/two/Same.ttf")
    forget_loaded()
    server.stop()
    assert load(server.url("/two/Same.ttf"), tmp_path).name == "Same~2.ttf"      # found again, offline


def test_a_file_that_is_there_without_an_index_entry_is_not_taken_for_the_address(tmp_path, server, fonts):
    folder = tmp_path / "sketch" / "fonts"
    folder.mkdir(parents=True)
    (folder / "Mine.ttf").write_bytes(fonts["ttf"])
    server.routes["/Mine.ttf"] = (200, fonts["ttf"])
    load(server.url("/Mine.ttf"), tmp_path)
    assert (folder / "Mine~2.ttf").exists() and len(server.hits) == 1


def test_a_deleted_copy_is_downloaded_again(tmp_path, server, fonts):
    server.routes["/Test.ttf"] = (200, fonts["ttf"])
    load(server.url("/Test.ttf"), tmp_path)
    (tmp_path / "sketch" / "fonts" / "Test.ttf").unlink()
    forget_loaded()
    load(server.url("/Test.ttf"), tmp_path)
    assert len(server.hits) == 2 and (tmp_path / "sketch" / "fonts" / "Test.ttf").exists()


def test_a_github_address_is_downloaded_from_the_raw_host(tmp_path, monkeypatch, fonts):
    asked = []
    web_fonts.set_url_fetcher(lambda address: asked.append(address) or fonts["ttf"])
    load("https://github.com/me/repo/blob/main/fonts/Test.ttf", tmp_path)
    assert asked == ["https://raw.githubusercontent.com/me/repo/main/fonts/Test.ttf"]
    sources = json.loads((tmp_path / "sketch" / "fonts" / "sources.json").read_text(encoding="utf-8"))
    assert sources == {"Test.ttf": "https://raw.githubusercontent.com/me/repo/main/fonts/Test.ttf"}


def test_text_font_takes_an_address(tmp_path, server, fonts):
    server.routes["/Test.ttf"] = (200, fonts["ttf"])
    sketch = api.active_sketch()
    sketch.text_font(server.url("/Test.ttf"), 30, base_dir=sketch_folder(tmp_path))
    assert sketch.style.font == "Test.ttf"
    assert (tmp_path / "sketch" / "fonts" / "Test.ttf").exists()


# ---------------------------------------------------------------- errors
def test_no_connection_on_the_first_run_is_a_plain_connection_error(tmp_path, server):
    address = server.url("/Test.ttf")
    server.stop()
    with pytest.raises(ConnectionError) as error:
        load(address, tmp_path)
    text = str(error.value)
    assert text.startswith(f"f.load_font(): could not download '{address}' (")
    assert text.endswith("). Run the sketch once while online; after that funground uses the copy in fonts/.")
    assert not (tmp_path / "sketch" / "fonts").exists()


def test_a_site_that_does_not_answer_in_time_is_a_timeout(tmp_path, server, fonts):
    server.routes["/Slow.ttf"] = (200, fonts["ttf"])
    server.slow.add("/Slow.ttf")
    address = server.url("/Slow.ttf")
    with pytest.raises(ConnectionError, match=r"could not download '.*Slow.ttf' \(timed out\)\. Run the sketch once while online"):
        load(address, tmp_path)


def test_404_says_there_is_no_font_there(tmp_path, server):
    address = server.url("/Nothing.ttf")
    with pytest.raises(FileNotFoundError) as error:
        load(address, tmp_path)
    assert str(error.value) == f"f.load_font(): there is no font at '{address}' (the site answered 404)."


def test_another_http_error_is_a_connection_error_with_the_status(tmp_path, server):
    server.routes["/Broken.ttf"] = (500, b"oops")
    address = server.url("/Broken.ttf")
    with pytest.raises(ConnectionError) as error:
        load(address, tmp_path)
    assert str(error.value) == f"f.load_font(): could not download '{address}' (the site answered 500)."


def test_something_that_is_not_a_font_is_refused_and_not_kept(tmp_path, server):
    server.routes["/page.html"] = (200, b"<html>not a font</html>")
    address = server.url("/page.html")
    with pytest.raises(ValueError, match=r"^f\.load_font\(\): '.*page\.html' is not a font funground can read"):
        load(address, tmp_path)
    folder = tmp_path / "sketch" / "fonts"
    assert not folder.exists() or list(folder.iterdir()) == []


def test_a_woff2_download_is_refused_in_one_plain_line_and_not_kept(tmp_path, server, fonts):
    server.routes["/x.woff2"] = (200, fonts["woff2"])
    with pytest.raises(ValueError) as error:
        load(server.url("/x.woff2"), tmp_path)
    assert str(error.value) == WOFF2_MESSAGE
    folder = tmp_path / "sketch" / "fonts"
    assert not folder.exists() or list(folder.iterdir()) == []


def test_a_woff2_file_on_disk_is_refused(tmp_path, fonts):
    (tmp_path / "x.woff2").write_bytes(fonts["woff2"])
    with pytest.raises(ValueError) as error:
        typography.load_font("x.woff2", str(tmp_path))
    assert str(error.value) == WOFF2_MESSAGE


def test_more_than_30_mb_is_refused(tmp_path, server, fonts, monkeypatch):
    assert web_fonts.MAX_BYTES == 30 * 1024 * 1024
    monkeypatch.setattr(web_fonts, "MAX_BYTES", 100)
    server.routes["/Big.ttf"] = (200, fonts["ttf"])
    with pytest.raises(ValueError, match="too big for a font"):
        load(server.url("/Big.ttf"), tmp_path)
    assert not (tmp_path / "sketch" / "fonts").exists()


# ---------------------------------------------------------------- WOFF
def test_a_woff_draws_the_same_outlines_as_the_ttf_of_the_same_font(tmp_path, fonts):
    (tmp_path / "Test.woff").write_bytes(fonts["woff"])
    plain = typography.load_font(str(fonts["ttf_path"]))
    packed = typography.load_font("Test.woff", str(tmp_path))
    a, b = plain._resource(), packed._resource()
    assert a.shape("ABCDE", 40).glyphs == b.shape("ABCDE", 40).glyphs
    assert [g.gid for g in b.shape("ABCDE", 40).glyphs] != [0] * 5                # not empty boxes
    gid = b.shape("B", 40).glyphs[0].gid
    assert a.outline(gid).segments == b.outline(gid).segments and a.outline(gid).segments
    assert typography.text_width("ABCDE", 40, b) == typography.text_width("ABCDE", 40, a) > 0


def test_a_woff_can_come_from_an_address(tmp_path, server, fonts):
    server.routes["/Test.woff"] = (200, fonts["woff"])
    font = load(server.url("/Test.woff"), tmp_path)
    assert font._resource().shape("A", 20).glyphs[0].gid != 0


# ---------------------------------------------------------------- the provider
METADATA = '''name: "Lorem"
designer: "A. Designer"
license: "OFL"
category: "SERIF"
date_added: "2011-01-01"
fonts {
  name: "Lorem"
  style: "normal"
  weight: 400
  filename: "Lorem-Regular.ttf"
  post_script_name: "Lorem-Regular"
  full_name: "Lorem Regular"
  copyright: "Copyright {c} 2011, a (b)"
}
fonts {
  name: "Lorem"
  style: "normal"
  weight: 700
  filename: "Lorem-Bold.ttf"
}
fonts {
  name: "Lorem"
  style: "italic"
  weight: 400
  filename: "Lorem-Italic.ttf"
}
subsets: "latin"
source {
  repository_url: "https://example.com/lorem"
  files {
    source_file: "OFL.txt"
    dest_file: "OFL.txt"
  }
}
'''

VARIABLE = '''name: "Vary"
fonts {
  name: "Vary"
  style: "normal"
  weight: 400
  filename: "Vary[wght].ttf"
}
fonts {
  name: "Vary"
  style: "italic"
  weight: 400
  filename: "Vary-Italic[wght].ttf"
}
axes {
  tag: "wght"
  min_value: 400.0
  max_value: 700.0
}
'''

MIXED = '''fonts {
  style: "normal"
  weight: 300
  filename: "Mix-Light.ttf"
}
fonts {
  style: "normal"
  weight: 900
  filename: "Mix-Black.ttf"
}
'''


def test_metadata_is_read_as_text():
    fonts, axes = web_fonts.parse_metadata(METADATA)
    assert fonts == [{"style": "normal", "weight": 400.0, "filename": "Lorem-Regular.ttf"},
                     {"style": "normal", "weight": 700.0, "filename": "Lorem-Bold.ttf"},
                     {"style": "italic", "weight": 400.0, "filename": "Lorem-Italic.ttf"}]
    assert axes == {}
    fonts, axes = web_fonts.parse_metadata(VARIABLE)
    assert [x["filename"] for x in fonts] == ["Vary[wght].ttf", "Vary-Italic[wght].ttf"]
    assert axes == {"wght": (400.0, 700.0)}


@pytest.mark.parametrize("text, weight, italic, wanted", [
    (METADATA, None, False, ("Lorem-Regular.ttf", None)),            # no weight: 400, and nothing to set
    (METADATA, 700, False, ("Lorem-Bold.ttf", None)),                # a static file of the exact weight wins
    (METADATA, 400, True, ("Lorem-Italic.ttf", None)),
    (METADATA, 600, False, ("Lorem-Bold.ttf", None)),                # nearest weight
    (METADATA, 300, False, ("Lorem-Regular.ttf", None)),
    (METADATA, 700, True, ("Lorem-Italic.ttf", None)),               # only one italic
    (VARIABLE, None, False, ("Vary[wght].ttf", None)),
    (VARIABLE, 700, False, ("Vary[wght].ttf", 700.0)),               # a variable file whose axis covers it
    (VARIABLE, 500, True, ("Vary-Italic[wght].ttf", 500.0)),
    (VARIABLE, 900, False, ("Vary[wght].ttf", 700.0)),               # nearest: the axis end
    (MIXED, 800, False, ("Mix-Black.ttf", None)),
    (MIXED, 100, False, ("Mix-Light.ttf", None)),
])
def test_the_file_is_chosen_by_style_then_weight(text, weight, italic, wanted):
    fonts, axes = web_fonts.parse_metadata(text)
    assert web_fonts.choose_file(fonts, axes, weight, italic) == wanted


def test_a_family_with_no_italic_has_no_choice():
    fonts, axes = web_fonts.parse_metadata(MIXED)
    assert web_fonts.choose_file(fonts, axes, None, True) is None


def test_the_family_folder_is_lower_case_without_spaces_and_hyphens():
    assert web_fonts.family_directory("EB Garamond") == "ebgaramond"
    assert web_fonts.family_directory("Roboto-Slab") == "robotoslab"


@pytest.fixture
def google(server, fonts, monkeypatch):
    """The google/fonts repository on the local server: a family 'Vary' (variable) under apache, and 'Lorem' under ofl."""
    monkeypatch.setattr(web_fonts, "GOOGLE_RAW", server.url("/google/fonts/main"))
    base = "/google/fonts/main"
    server.routes[f"{base}/apache/vary/METADATA.pb"] = (200, VARIABLE.encode())
    server.routes[f"{base}/apache/vary/Vary[wght].ttf"] = (200, fonts["variable"])
    server.routes[f"{base}/apache/vary/Vary-Italic[wght].ttf"] = (200, fonts["variable"])
    server.routes[f"{base}/ofl/lorem/METADATA.pb"] = (200, METADATA.encode())
    server.routes[f"{base}/ofl/lorem/Lorem-Bold.ttf"] = (200, fonts["ttf"])
    server.routes[f"{base}/ofl/lorem/Lorem-Regular.ttf"] = (200, fonts["ttf"])
    return server


def test_a_provider_finds_a_family_and_keeps_its_files(tmp_path, google):
    font = load("Lorem", tmp_path, provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS, weight=700)
    folder = tmp_path / "sketch" / "fonts"
    assert font.name == "Lorem-Bold.ttf" and font.family() == "TestStatic"
    assert sorted(p.name for p in folder.iterdir()) == ["Lorem-Bold.ttf", "lorem.METADATA.pb", "sources.json"]
    sources = json.loads((folder / "sources.json").read_text(encoding="utf-8"))
    assert sources["Lorem-Bold.ttf"] == google.url("/google/fonts/main/ofl/lorem/Lorem-Bold.ttf")
    assert sources["lorem.METADATA.pb"] == google.url("/google/fonts/main/ofl/lorem/METADATA.pb")


def test_the_licence_folders_are_tried_in_order(tmp_path, google):
    load("Vary", tmp_path, provider="google_fonts")
    assert google.hits[:2] == ["/google/fonts/main/ofl/vary/METADATA.pb", "/google/fonts/main/apache/vary/METADATA.pb"]


def test_a_provider_also_works_on_the_second_run_offline(tmp_path, google):
    options = dict(provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS, weight=700)
    first = load("Vary", tmp_path, **options)
    google.stop()
    forget_loaded()
    second = load("Vary", tmp_path, **options)
    assert first.name == second.name == "Vary[wght].ttf@wght=700"
    assert len(google.hits) == 3                                     # ofl 404, apache metadata, the font: once


def test_a_variable_font_with_a_weight_draws_at_that_weight_by_default(tmp_path, google):
    plain = load("Vary", tmp_path, provider="google_fonts")
    bold = load("Vary", tmp_path, provider="google_fonts", weight=700)
    assert plain.name == "Vary[wght].ttf" and bold.name == "Vary[wght].ttf@wght=700"
    assert plain != bold
    assert plain._resource().location(()) == ()
    assert bold._resource().location(()) == (("wght", 700.0),)
    assert bold._resource().shape("A", 20).location == (("wght", 700.0),)
    assert plain._resource().outline(plain._resource().shape("A", 20).glyphs[0].gid) != \
        bold._resource().outline(bold._resource().shape("A", 20).glyphs[0].gid, (("wght", 700.0),))


def test_font_variations_override_the_default_axis_by_axis(tmp_path, google):
    resource = load("Vary", tmp_path, provider="google_fonts", weight=700)._resource()
    assert resource.location((("wght", 300),)) == (("wght", 300.0),)
    assert resource.location((("wdth", 50),)) == (("wght", 700.0),)           # an axis the font lacks is ignored
    assert resource.shape("A", 20, variations=(("wght", 300),)).location == (("wght", 300.0),)
    assert resource.defaults == (("wght", 700.0),)


def test_italic_picks_the_italic_file(tmp_path, google):
    font = load("Vary", tmp_path, provider="google_fonts", italic=True)
    assert font.name == "Vary-Italic[wght].ttf"


def test_a_static_family_ignores_the_default_location(tmp_path, google):
    assert load("Lorem", tmp_path, provider="google_fonts", weight=400).name == "Lorem-Regular.ttf"


def test_a_family_that_is_not_there_says_so(tmp_path, google):
    with pytest.raises(FileNotFoundError) as error:
        load("Nothing Here", tmp_path, provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS)
    assert str(error.value) == "f.load_font(): Google Fonts has no family called 'Nothing Here'."
    assert not (tmp_path / "sketch" / "fonts").exists()


def test_a_family_without_the_style_says_so(tmp_path, google):
    google.routes["/google/fonts/main/ofl/mix/METADATA.pb"] = (200, MIXED.encode())
    with pytest.raises(FileNotFoundError, match="the Google Fonts family 'Mix' has no italic font"):
        load("Mix", tmp_path, provider="google_fonts", italic=True)


def test_weight_and_italic_need_a_provider(tmp_path, fonts):
    for options in ({"weight": 700}, {"italic": True}):
        with pytest.raises(TypeError, match=r"weight and italic .* provider="):
            typography.load_font(str(fonts["ttf_path"]), None, **options)


def test_a_wrong_provider_or_weight_is_refused(tmp_path, google):
    with pytest.raises(ValueError, match="provider must be one of 'google_fonts'"):
        load("Vary", tmp_path, provider="fontshop")
    with pytest.raises(TypeError, match="weight is a number"):
        load("Vary", tmp_path, provider="google_fonts", weight="bold")
    with pytest.raises(ValueError, match="1 to 1000"):
        load("Vary", tmp_path, provider="google_fonts", weight=0)
    with pytest.raises(TypeError, match="italic is True or False"):
        load("Vary", tmp_path, provider="google_fonts", italic="yes")


def test_the_provider_constant_is_the_word():
    assert f.CONSTANTS.PROVIDERS.GOOGLE_FONTS == "google_fonts"
    assert list(f.CONSTANTS.PROVIDERS) == ["google_fonts"]


# ---------------------------------------------------------------- f.keep()
KEEP_SKETCH = '''
import funground as f
f.size(200, 100)
f.text_font(f.load_font({address!r}), 20)
f.text("AB", 10, 10)
f.keep()
'''


def run_file(folder, source):
    path = Path(folder) / "sketch.py"
    path.write_text(source, encoding="utf-8")
    exec(compile(source, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})


def test_keep_records_where_a_web_font_came_from(tmp_path, server, fonts, monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    monkeypatch.chdir(tmp_path)
    server.routes["/a/Test.ttf"] = (200, fonts["ttf"])
    address = server.url("/a/Test.ttf")
    run_file(tmp_path, KEEP_SKETCH.format(address=address))
    record = json.loads((tmp_path / "studio" / "001.json").read_text(encoding="utf-8"))
    assert record["fonts"] == {"Test.ttf": address}
    assert (tmp_path / "fonts" / "Test.ttf").exists()


def test_keep_leaves_out_fonts_when_there_is_no_web_font(tmp_path, monkeypatch):
    monkeypatch.setenv("FUNGROUND_HEADLESS", "1")
    monkeypatch.chdir(tmp_path)
    run_file(tmp_path, "import funground as f\nf.size(50, 50)\nf.text('hi', 5, 5)\nf.keep()\n")
    record = json.loads((tmp_path / "studio" / "001.json").read_text(encoding="utf-8"))
    assert "fonts" not in record


# ---------------------------------------------------------------- the browser host
def test_the_host_fetcher_is_used_instead_of_urllib(tmp_path, fonts, monkeypatch):
    monkeypatch.setattr(web_fonts, "_download_urllib", lambda address: pytest.fail("urllib was used"))
    asked = []
    session = Session(320, 200, fetch_url=lambda address: asked.append(address) or fonts["ttf"])
    try:
        font = load("https://fonts.example/Test.ttf", tmp_path)
        assert font.family() == "TestStatic" and asked == ["https://fonts.example/Test.ttf"]
        assert (tmp_path / "sketch" / "fonts" / "Test.ttf").read_bytes() == fonts["ttf"]
    finally:
        session.stop()


def test_a_host_fetcher_can_return_something_with_to_bytes(tmp_path, fonts):
    class Proxy:
        def to_bytes(self):
            return fonts["ttf"]

    session = Session(320, 200, fetch_url=lambda address: Proxy())
    try:
        assert load("https://fonts.example/Test.ttf", tmp_path).family() == "TestStatic"
    finally:
        session.stop()


def test_a_host_failure_becomes_one_plain_connection_error(tmp_path):
    def refuse(address):
        raise RuntimeError("TypeError: Failed to fetch")

    session = Session(320, 200, fetch_url=refuse)
    try:
        with pytest.raises(ConnectionError) as error:
            load("https://fonts.example/Test.ttf", tmp_path)
        assert str(error.value) == ("f.load_font(): the browser could not download 'https://fonts.example/Test.ttf'. "
                                    "The site may not allow it, or there is no connection. Download the file and use Add file.")
        assert "Failed to fetch" not in str(error.value)
    finally:
        session.stop()


def test_a_session_without_a_host_fetcher_goes_back_to_urllib(tmp_path, server, fonts):
    first = Session(320, 200, fetch_url=lambda address: pytest.fail("the old host was asked"))
    first.stop()
    second = Session(320, 200)
    try:
        server.routes["/Test.ttf"] = (200, fonts["ttf"])
        assert load(server.url("/Test.ttf"), tmp_path).name == "Test.ttf"
    finally:
        second.stop()


# ---------------------------------------------------------------- the real network (optional)
def online() -> bool:
    try:
        socket.create_connection(("raw.githubusercontent.com", 443), timeout=3).close()
        return True
    except OSError:
        return False


def test_google_fonts_provider_against_the_real_repository(tmp_path, monkeypatch):
    """Notices if the layout of google/fonts (ofl/<name>/METADATA.pb) changes. Skipped when there is no internet."""
    if not online():
        pytest.skip("no internet")
    monkeypatch.setattr(web_fonts, "TIMEOUT", 20.0)
    font = load("Lora", tmp_path, provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS, weight=700)
    assert font.name == "Lora[wght].ttf@wght=700" and font.family() == "Lora"
    low, normal, high = font.variations()["wght"]
    assert low <= 700 <= high
    sources = json.loads((tmp_path / "sketch" / "fonts" / "sources.json").read_text(encoding="utf-8"))
    assert sources["Lora[wght].ttf"] == "https://raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora%5Bwght%5D.ttf"
