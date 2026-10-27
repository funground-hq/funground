# Web fonts (S-230, D-117, D-119)

**Status:** measured 27 October 2026; the proposal accepted as D-119 the same day; being built (S-230).

## Problem

A learner finds a font on the web and wants to use it. Today they download the file, put it beside the sketch and
call `f.load_font("Lora.ttf")`; in Play they use Add file. D-117 a (accepted 20 Oct) lets `load_font()` and
`text_font()` take a web address of a font file instead, downloaded once and kept so a second run works offline,
and allows a provider as an option word (never a function named after a company), such as
`f.CONSTANTS.PROVIDERS.GOOGLE_FONTS`, to find a family by name.

## Measurements (27 Oct 2026)

**Which hosts a browser may fetch from.** A font in Play is fetched by the runner's worker, so the host must send
`Access-Control-Allow-Origin`. Checked with curl and an `Origin: https://funground-hq.github.io` header:

| Address | Status | CORS | Type |
|---|---|---|---|
| `raw.githubusercontent.com/google/fonts/main/ofl/lora/Lora[wght].ttf` | 200 | `*` | octet-stream |
| `github.com/google/fonts/raw/main/...` (what a learner copies from GitHub) | 302 to the address above | **empty: the browser refuses it** | |
| `cdn.jsdelivr.net/gh/google/fonts@main/ofl/lora/Lora[wght].ttf` | 200 | `*` | font/ttf |
| `fonts.googleapis.com/css2?family=Lora` (the Google Fonts stylesheet) | 200 | `*` | text/css |
| `fonts.gstatic.com/s/lora/v37/....ttf` (a file the stylesheet names) | 200 | `*` | font/ttf |
| `cdn.jsdelivr.net/fontsource/fonts/lora@latest/latin-400-normal.ttf` (Fontsource) | 200 | `*` | font/ttf |

**Google's stylesheet chooses the format from the browser.** Asked by curl it names `.ttf` files; asked with a
browser's User-Agent it names `.woff2`. A request from Play's worker carries the browser's User-Agent, which a page
cannot change, so in Play the stylesheet would lead to WOFF2.

**Which formats funground reads** (Lora 400 from Fontsource, desktop, Python 3.14):

| Format | Size | `load_font()` | Drawn |
|---|---|---|---|
| TTF | 47,652 B | loads | correct |
| WOFF | 25,960 B | **loads** | **empty boxes, no error** (a bug, below) |
| WOFF2 | 21,148 B | `ValueError` "No module named brotli" | — |

**The WOFF bug.** fontTools unpacks a WOFF file itself, so `load_font()` succeeds, but `FontResource` hands the
file's raw, still-compressed bytes to HarfBuzz, which finds no glyphs: every letter is glyph 0. Contract T11 says
`load_font()` reads `.ttf` and `.otf` and that a file that is not a font gives `ValueError`, so today's behaviour
breaks the contract. Fix either way: refuse WOFF with a plain `ValueError`, or give HarfBuzz the unpacked font
(`TTFont.flavor = None`, then save to bytes), which needs no new dependency.

**WOFF2** needs the Brotli package to unpack. Pyodide 314.0.7 ships `brotli`; the desktop install does not have it
(it would be a new runtime dependency, a maintainer decision).

**An address today** is treated as a file path: `load_font("https://...ttf")` gives `FileNotFoundError` naming a
path made of the sketch's folder and the address. There is no network code in funground.

**Finding a family by name.** Google's own repository `google/fonts` has a `METADATA.pb` per family, readable as
text, listing each file with its style and weight (Lora: `Lora[wght].ttf` normal, `Lora-Italic[wght].ttf` italic,
both variable fonts). The family's folder is `ofl/<name in lower case without spaces>/` for almost every family
(`apache/` and `ufl/` for a few).

## Proposal (D-119)

1. **No new argument for an address.** Where `load_font()` and `text_font()` take a path, a string starting with
   `http://` or `https://` is an address. A `github.com/<owner>/<repo>/(blob|raw)/...` address is read from
   `raw.githubusercontent.com`, because that is what learners copy and the browser refuses the other.
2. **The copy is kept beside the sketch**, in a `fonts/` folder, under the file's own name. The sketch then works
   offline and travels with its font (the licences of Google's fonts, OFL, Apache and UFL, allow this). A second run
   uses the copy without asking the network. In Play the copy goes to My files (S-221), so it is kept the same way.
3. **A provider finds a family by name:** `load_font("Lora", provider=f.CONSTANTS.PROVIDERS.GOOGLE_FONTS)`, with
   `weight=` and `italic=` choosing among the family's files (a variable font is set with the existing variations,
   T18). It reads Google's own repository through `raw.githubusercontent.com` (`METADATA.pb`, then the `.ttf`), not
   the stylesheet, so it gets TTF on the desktop and in Play alike. The only provider word at first is
   `GOOGLE_FONTS`.
4. **Formats:** TTF and OTF, as now; WOFF read by unpacking it for HarfBuzz (fixing the bug); WOFF2 refused with one
   plain line that says to use the `.ttf` (no Brotli dependency).
5. **Errors, one plain line each:** no connection on the first run ("could not download ...; run it once while
   online, then funground uses the copy in fonts/"); an address that is not a font (the existing `ValueError`); a
   host that refuses the browser (Play only: "this site does not let the browser download fonts; download the file
   and use Add file"); a family the provider does not have.
6. **`f.keep()`** records the address or the provider and family, so a kept sketch says where its font came from.

## Rejected

- **Google's stylesheet API** for the provider: WOFF2 in browsers, and it ties the lookup to a page format meant
  for CSS.
- **Fontsource** for the provider: TTF with CORS, but per-subset static files (`latin-400-normal`), so Devanagari
  and other scripts need a second lookup, and it is a mirror, not Google's own source.
- **A hidden cache folder** for the copy: it works offline on this computer, but the sketch does not carry its font
  to another one, and a learner cannot see what was downloaded.
- **`f.google_font()`** and any function named after a provider (D-117).

## Limits

The provider needs the network the first time, and Google's repository layout (`ofl/<name>/METADATA.pb`) is a
convention, not an API: a test runs against a fixed family to notice if it changes. jsDelivr and GitHub are
reachable from Play today; a school network that blocks them gets the plain error of point 5.

## Tests (planned)

A local HTTP server serves a TTF, a WOFF, a WOFF2, a non-font and a slow or failing response; tests cover the
download, the kept copy and the second run offline, the GitHub address rewrite, each error, and `f.keep()`. The
browser runner gets a scenario with a served font. The provider is tested against a recorded `METADATA.pb`; one
network test, skipped offline, checks the real repository.
