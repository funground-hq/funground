"""The gallery browser now lives in the package: ``python -m funground.gallery`` (S-103).

This file stays so ``python tools/gallery_browser.py`` keeps working in a checkout.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))      # run from a checkout, installed or not

from funground.gallery import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
