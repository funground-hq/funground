"""How small can a colour emoji font get? Subsets of Noto Color Emoji (COLRv1) and Twemoji (COLRv0)."""
import io, os, zlib, logging, regex
from fontTools.ttLib import TTFont
from fontTools import subset
logging.disable(logging.WARNING)
from fb import FONTS
EP = {c for c in range(0x110000) if regex.match(r"\p{Emoji_Presentation}", chr(c))}
for fn in ("Twemoji.Mozilla.ttf", "NotoColorEmoji-Regular.ttf"):
    for label, unis in (("whole cmap", None), ("Emoji_Presentation chars only", EP), ("~100 common emoji (U+1F600-1F64F + few)", set(range(0x1F600, 0x1F650)))):
        t = TTFont(os.path.join(FONTS, fn))
        if unis is not None:
            o = subset.Options(); o.layout_features = ["*"]; o.hinting = False; o.glyph_names = False
            s = subset.Subsetter(o); s.populate(unicodes=unis); s.subset(t)
        b = io.BytesIO(); t.save(b); raw = b.getvalue()
        print(f"{fn:30}{label:44}{len(raw)/1e6:7.2f} MB raw {len(zlib.compress(raw, 6))/1e6:7.2f} MB zlib")
