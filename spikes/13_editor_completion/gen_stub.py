"""Spike: build typings/funground/__init__.pyi from inspect.signature of funground's public names."""
import inspect, re, sys, pathlib, ast
import funground as f
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
src = pathlib.Path(f.__file__).read_text(encoding="utf-8")
m = re.search(r"if TYPE_CHECKING:\n(.*?)\n\n# What", src, re.S)     # the live values
live = [l.strip() for l in m.group(1).splitlines() if re.match(r"\s+\w+: ", l)]
liven = {l.split(":")[0] for l in live}

def ann(a):
    return a.strip("'") if isinstance(a, str) else "Any"

def fmt(sg, skip_self=False):
    ps, star_seen = [], False
    for p in sg.parameters.values():
        if p.kind == p.VAR_POSITIONAL: star_seen = True
        if p.kind == p.KEYWORD_ONLY and not star_seen: ps.append("*"); star_seen = True
        s = {p.VAR_POSITIONAL: "*", p.VAR_KEYWORD: "**"}.get(p.kind, "") + p.name
        if p.annotation is not p.empty: s += ": " + ann(p.annotation)
        if p.default is not p.empty: s += (" = " if p.annotation is not p.empty else "=") + repr(p.default)
        ps.append(s)
    r = ann(sg.return_annotation) if sg.return_annotation is not sg.empty else "Any"
    return ps, r

lines = ["from typing import Any", "Color = Any", "class Ground: ...", ""] + live + [""]
for n in sorted(f._PUBLIC_NAMES):
    if n in liven: continue
    o = getattr(f, n, None)
    doc = (inspect.getdoc(o) or "").split("\n")[0].replace('"""', "'") if o is not None else ""
    try: ps, r = fmt(inspect.signature(o))
    except (TypeError, ValueError): ps, r = ["*args: Any", "**kwargs: Any"], "Any"
    if o is None: lines.append(f"{n}: Any")
    elif inspect.isclass(o):
        lines += [f"class {n}:", f'    """{doc}"""', f"    def __init__({', '.join(['self'] + ps)}) -> None: ..."]
    elif callable(o):
        lines += [f"def {n}({', '.join(ps)}) -> {r}:", f'    """{doc}"""', "    ..."]
    else: lines.append(f"{n}: Any")
allnames = ast.literal_eval(re.search(r"__all__ = (\[.*?\])", src, re.S).group(1))
lines.append("__all__ = " + repr(allnames))
(out / "__init__.pyi").write_text("\n".join(lines) + "\n", encoding="utf-8")
