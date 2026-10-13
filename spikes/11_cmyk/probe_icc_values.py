"""Probe 4: what the ICC route does to key colours (sRGB -> Windows 'Swop Standard' CMYK, relative colorimetric + BPC),
 vs the naive formula. Values are percentages C M Y K."""
import sys, warnings, time, os
warnings.simplefilter("ignore")
from PIL import Image, ImageCms
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rgb_to_cmyk as m
t = ImageCms.buildTransform(ImageCms.createProfile("sRGB"), ImageCms.getOpenProfile(sys.argv[1]), "RGB", "CMYK",
        renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC, flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)
cols = {"black 0,0,0": (0,0,0), "white": (255,255,255), "grey 128": (128,128,128), "red": (255,0,0), "lime 0,255,0": (0,255,0),
        "blue": (0,0,255), "gold": (255,215,0), "tomato": (255,99,71), "midnightblue": (25,25,112)}
for name, rgb in cols.items():
    px = ImageCms.applyTransform(Image.new("RGB", (1, 1), rgb), t).getpixel((0, 0))
    n = m.naive(*[v/255 for v in rgb])
    print(f"{name:15} icc {[round(v/2.55) for v in px]}  naive {[round(v*100) for v in n]}")
# speed: 300 dpi A4 = 2480x3508
im = Image.effect_noise((2480, 3508), 60).convert("RGB")
t0 = time.time(); ImageCms.applyTransform(im, t); print("lcms 8.7 Mpx:", round(time.time()-t0, 2), "s")
