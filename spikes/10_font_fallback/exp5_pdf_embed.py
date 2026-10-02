"""T15 check: do separate Text ops in different fonts each embed their own subset with the CURRENT code?
Runs funground read-only from the project venv (PYTHONDONTWRITEBYTECODE=1); only writes into out/."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import funground as f
F = os.path.join(HERE, "fonts")
f.size(640, 260)
f.background(255)
f.fill(0)
f.text_size(28)
rows = [
    (None, "DejaVu: Hello wörld € → ★ 😀", 10),
    ("NotoSansDevanagari-Regular.ttf", "हिन्दी नमस्ते", 50),
    ("NotoSansArabic-Regular.ttf", "مرحبا بالعالم", 90),
    ("NotoSansSymbols2-Regular.ttf", "\U0001F3B2 \U0001F9ED ⮩ \U0001FA90", 130),
    ("NotoEmoji-VF.ttf", "\U0001F600 \U0001F680 ❤", 170),
    ("NotoSansJP-Subset.otf", "日本語のテキスト 你好", 210),
]
for fname, s, y in rows:
    if fname:
        f.text_font(f.load_font(os.path.join(F, fname)))
    f.text(s, 10, y)
f.save(os.path.join(HERE, "out", "exp5_multi_font.pdf"))
f.save(os.path.join(HERE, "out", "exp5_multi_font.png"))
