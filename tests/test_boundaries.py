"""Provider boundary (story S-017): pygame is imported only by providers.

The architecture rule "backend types stay behind providers" is enforced here
so it cannot erode. Extend ALLOWED when a new provider package is added.
"""
from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "funground"
BACKENDS = {"pygame", "cairo", "skia", "blend2d", "moderngl", "OpenGL", "pathops", "svgelements", "pypdf", "imageio_ffmpeg"}
# Which backend each provider directory may import (S-026: pygame is platform-only now).
# imaging.py reads image files with pygame-ce (ADR-004, D-028).
ALLOWED = {"platform/": {"pygame"}, "renderers/": {"cairo", "skia", "blend2d", "pygame"}, "export/": {"cairo", "pypdf", "imageio_ffmpeg"},             # pypdf: real PDF text (D-043)
           "imaging.py": {"pygame"},
           "sound.py": {"pygame"},                           # sound playback (D-046)
           "microphone_input.py": {"pygame"},                     # microphone input via pygame._sdl2.audio (D-058)
           "pathops.py": {"pathops"},                        # path booleans (ADR-005, D-037)
           "svg.py": {"svgelements"}}                       # SVG import (D-041)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def test_backend_libraries_are_imported_only_by_providers():
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        rel = path.relative_to(PACKAGE).as_posix()
        allowed = next((libs for prefix, libs in ALLOWED.items() if rel.startswith(prefix)), set())
        hit = (_imports(path) & BACKENDS) - allowed
        if hit:
            offenders.append(f"{rel}: {sorted(hit)}")
    assert not offenders, "backend imports outside their provider:\n" + "\n".join(offenders)


def test_no_pygame_drawing_remains():
    """D-008: pygame draws nothing after the legacy renderer is deleted."""
    for path in PACKAGE.rglob("*.py"):
        src = path.read_text(encoding="utf-8")
        assert "pygame.draw" not in src and "pygame.font" not in src, path.name


def test_public_facade_imports_no_backend():
    for name in ("api.py", "__init__.py", "sketch.py", "state.py", "color.py"):
        assert not (_imports(PACKAGE / name) & BACKENDS), name
