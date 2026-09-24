# playground v0.5

A tiny teaching wrapper around `pygame-ce`.

## Folder layout

For the simplest classroom use, copy the **whole `playground` folder** beside the learner's script:

```text
python-dsf/
├── hello_visual.py
└── playground/
    ├── __init__.py
    └── _core.py
```

The `__init__.py` file is important. Without it, Python may treat the folder as a namespace package; `import playground` can then succeed while `playground.run` is missing.

Install the only external dependency:

```powershell
python -m pip install pygame-ce
```

## Example

```python
import playground as p

x = 50


def setup():
    p.size(640, 400)


def draw():
    global x

    p.background("white")
    p.fill("tomato")
    p.circle(x, p.height / 2, 40)
    x += 2


p.run()
```

`p.run()` automatically looks for `setup()` and `draw()` in the calling script. `setup()` is optional; `draw()` is required.

Live values are module attributes, e.g. `p.width`, `p.height`, `p.mouse_x`, `p.frame_count`, and `p.delta_time`.

## Quick diagnostic

```powershell
python -c "import playground; print(playground.__file__); print(playground.__version__); print(playground.run)"
```

For a local copy, `playground.__file__` should end in `playground\\__init__.py`, the version should be `0.5.0`, and `playground.run` should print as a function.
