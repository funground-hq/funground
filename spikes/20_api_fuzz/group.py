"""Group findings.jsonl by class, exception and top funground frame; print a Markdown table."""
import collections
import json
import sys


def top_frame(res):
    if not res:
        return "-"
    frames = res.get("frames") or []
    if not frames:
        for kind, ext, msg, fr in res.get("files", []):
            frames = fr or frames
    inside = [f for f in frames if f[0].startswith("funground")]
    if not inside:
        return "-"
    fr = inside[-1]
    return f"{fr[0]}:{fr[1]} {fr[2]}"


def main(paths):
    groups = collections.defaultdict(list)
    for p in paths:
        for line in open(p):
            r = json.loads(line)
            res = r["res"] or {}
            exc = res.get("type") or r["why"]
            if res.get("status") == "ok":
                exc = r["why"]
            groups[(r["class"], exc.split(":")[0][:80], top_frame(res))].append(r)
    for (cls, exc, frame), rs in sorted(groups.items(), key=lambda kv: (kv[0][0], -len(kv[1]))):
        short = min(rs, key=lambda r: len(r["src"]))
        names = sorted({r["name"] for r in rs})
        msg = ((short["res"] or {}).get("msg") or short["why"])[:200].replace("\n", " ")
        print(json.dumps({"class": cls, "n": len(rs), "exc": exc, "frame": frame, "names": names[:12],
                          "repro": short["src"], "msg": msg}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
