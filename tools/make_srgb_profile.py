"""Make funground/data/sRGB.icc, the sRGB colour profile that every PDF is tagged with (story S-170).

    .venv/Scripts/python tools/make_srgb_profile.py

Run it once, on a developer machine with Pillow; the result is committed. The product never runs
this: Pillow is optional for funground, and the browser's Pillow has no ImageCms.

The profile comes from littleCMS (the colour engine inside Pillow's ImageCms, MIT licence), which builds
a standard sRGB matrix profile from the sRGB primaries and curve in IEC 61966-2-1. The bytes it
returns carry no third-party copyright: littleCMS writes "No copyright, use freely" into the profile.
See THIRD_PARTY_LICENSES.md and docs/design/Colour_For_Print_Note.md.
"""
from __future__ import annotations

from pathlib import Path

from PIL import ImageCms

TARGET = Path(__file__).resolve().parent.parent / "funground" / "data" / "sRGB.icc"


def main() -> None:
    made = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    data = made.tobytes()
    TARGET.write_bytes(data)
    print(f"wrote {TARGET} ({len(data)} bytes)")
    print("description:", ImageCms.getProfileDescription(made).strip())
    print("copyright:", ImageCms.getProfileCopyright(made).strip())


if __name__ == "__main__":
    main()
