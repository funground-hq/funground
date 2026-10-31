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
           "sound/_engine.py": {"pygame"},                   # sound playback (D-046)
           "sound/_microphone.py": {"pygame"},               # microphone input via pygame._sdl2.audio (D-058)
           "camera_input.py": {"pygame"},                         # camera input via pygame.camera (D-089)
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


def _library_imports(path: Path) -> set[str]:
    """Which of "sound" and "sangeet" a file imports from funground (relative or absolute)."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            base = (node.module or "").split(".")
            paths = [base + [a.name] for a in node.names]
            relative = node.level > 0
        elif isinstance(node, ast.Import):
            paths = [a.name.split(".") for a in node.names]
            relative = False
        else:
            continue
        for tokens in paths:
            if relative or tokens[0] == "funground":
                found |= {t for t in ("sound", "sangeet") if t in tokens[:3]}
    return found


def test_the_core_imports_neither_library():
    """S-246, ADR-007: nothing outside funground/sound/ and funground/sangeet/ imports them (funground/__init__.py
    only names them in its table of moved names), and only sangeet imports sound."""
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        rel = path.relative_to(PACKAGE).as_posix()
        hits = _library_imports(path)
        allowed = {"sound": {"sound"}, "sangeet": {"sound", "sangeet"}}
        library = rel.split("/")[0] if "/" in rel else None
        if hits - allowed.get(library, set()):
            offenders.append(f"{rel}: {sorted(hits)}")
    assert not offenders, "imports of a library from the core:\n" + "\n".join(offenders)
