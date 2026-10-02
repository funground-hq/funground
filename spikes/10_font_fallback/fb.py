"""Prototype of font fallback for funground (spike only; mirrors funground.typography.FontResource.shape)."""
import os
import regex
import uharfbuzz as hb
from fontTools.ttLib import TTFont, TTCollection

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
DEJAVU = os.path.join(HERE, "..", "..", "funground", "fonts", "DejaVuSans.ttf")

# Characters that join a cluster but are never drawn by themselves: they must not decide the font.
NEUTRAL = {0x200C, 0x200D, 0x200E, 0x200F, 0x2060, *range(0xFE00, 0xFE10), *range(0xE0100, 0xE01F0),
           *range(0xE0020, 0xE0080)}
GRAPHEME = regex.compile(r"\X")      # reference only (the `regex` package); the prototype uses clusters()


class Face:
    def __init__(self, path, number=0):
        self.path = path
        self.name = os.path.basename(path)
        tt = TTCollection(path).fonts[number] if path.endswith(".ttc") else TTFont(path)
        self.upem = tt["head"].unitsPerEm
        self.ascent = tt["hhea"].ascent
        self.cmap = frozenset(tt.getBestCmap())
        self.tt = tt
        blob = hb.Blob.from_file_path(path) if not path.endswith(".ttc") else hb.Blob(open(path, "rb").read())
        self.hbfont = hb.Font(hb.Face(blob, number))
        self.hbfont.scale = (self.upem, self.upem)

    def has_all(self, text):
        return all(ord(c) in self.cmap for c in text if ord(c) not in NEUTRAL and c != "\n")

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {"kern": True, "liga": True})
        return [(i.codepoint, p.x_advance, i.cluster) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


import unicodedata

REGIONAL = range(0x1F1E6, 0x1F200)
SKIN = range(0x1F3FB, 0x1F400)


def clusters(text):
    """Stdlib-only approximation of extended grapheme clusters: base + marks/ZWJ/VS/tags/skin tones,
    ZWJ and virama join the next character, regional indicators pair up, CRLF stays together."""
    out, i, n = [], 0, len(text)
    while i < n:
        j = i + 1
        if text[i] == chr(13) and j < n and text[j] == chr(10):
            j += 1
        else:
            ri = ord(text[i]) in REGIONAL
            while j < n:
                c, cp = text[j], ord(text[j])
                prev = ord(text[j - 1])
                if (unicodedata.category(c) in ("Mn", "Mc", "Me") or cp in NEUTRAL or cp in SKIN
                        or prev == 0x200D or unicodedata.combining(text[j - 1]) == 9 and unicodedata.category(c) == "Lo"
                        or ri and cp in REGIONAL and j == i + 1):
                    j += 1
                else:
                    break
        out.append((i, j))
        i = j
    return out


def itemise(text, chain, takes_neutral=lambda face: "Emoji" not in face.name and "Symbols" not in face.name,
            segment=clusters):
    """Runs (start, end, face_index): per cluster, the first face with every character.
    Spaces and punctuation stay with the previous run when that face has them and is a text face
    (an emoji font's space is 1.27 em wide), so a Devanagari or Arabic phrase is one run."""
    runs = []
    for a, b in segment(text):
        cl = text[a:b]
        pick = next((i for i, f in enumerate(chain) if f.has_all(cl)), 0)     # none: tofu from the primary
        if runs and pick != runs[-1][2] and all(not c.isalnum() for c in cl):
            prev = chain[runs[-1][2]]
            if takes_neutral(prev) and prev.has_all(cl):
                pick = runs[-1][2]
        if runs and runs[-1][2] == pick:
            runs[-1][1] = b
        else:
            runs.append([a, b, pick])
    return [tuple(r) for r in runs]


def shape_itemised(text, chain):
    if chain[0].has_all(text):                       # the fast path: nothing missing, today's code exactly
        return [(0, len(text), 0, chain[0].shape(text))]
    return [(a, b, i, chain[i].shape(text[a:b])) for a, b, i in itemise(text, chain)]


def shape_notdef(text, chain):
    """HarfBuzz-style: shape the whole string with the primary, re-shape the .notdef clusters with the next
    font (and so on); the good stretches are kept as one run each."""
    out, pending = [], [(0, len(text))]
    for fi, face in enumerate(chain):
        nxt = []
        for a, b in pending:
            g = face.shape(text[a:b])
            bad = {c for gid, adv, c in g if gid == 0}
            if fi == len(chain) - 1 or not bad:
                out.append((a, b, fi, g)); continue
            starts = sorted({c for _, _, c in g})
            ends = {s: (starts[k + 1] if k + 1 < len(starts) else b - a) for k, s in enumerate(starts)}
            good = []
            for s in starts:
                bucket = nxt if s in bad else good
                if bucket and bucket[-1][1] == a + s: bucket[-1] = (bucket[-1][0], a + ends[s])
                else: bucket.append((a + s, a + ends[s]))
            for ga, gb in good:
                out.append((ga, gb, fi, face.shape(text[ga:gb])))
        pending = nxt
        if not pending: break
    return sorted(out)


def chain_default():
    f = lambda n: Face(os.path.join(FONTS, n))
    return [Face(DEJAVU), f("NotoSansSymbols2-Regular.ttf"), f("NotoEmoji-VF.ttf"), f("NotoSansDevanagari-Regular.ttf"),
            f("NotoSansArabic-Regular.ttf"), f("NotoSansHebrew-Regular.ttf"), f("NotoSansJP-Subset.otf")]
