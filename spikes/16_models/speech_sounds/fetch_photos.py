"""Finds public-domain / CC0 photos on Wikimedia Commons for the kNN test and downloads 640 px copies.

    fetch_photos.py OUT_DIR            (OUT_DIR must be new; pictures stay out of the repo, only SOURCES go in)

Per class it searches Commons file pages, keeps jpg files whose licence is CC0 or Public domain, and writes
OUT_DIR/<class>_<n>.jpg plus OUT_DIR/sources.json (title, page URL, artist, licence). Slow on purpose (Commons rate limits).
"""
import json, os, re, sys, time, urllib.parse, urllib.request

UA = "funground-spike/0.1 (https://github.com/funground-hq; samirajoshi@gmail.com)"
API = "https://commons.wikimedia.org/w/api.php"
CLASSES = {"cat": ["tabby cat", "cat sitting", "Felis catus", "kitten", "cat lying"], "dog": ["labrador retriever", "dog sitting", "golden retriever", "German shepherd dog", "puppy"], "bird": ["Passer domesticus", "Columba livia", "Ardea cinerea", "Larus argentatus", "Parus major", "Anas platyrhynchos"]}
BAD = re.compile(r"portrait|painting|self|WGA|Art Project|museum|specimen|drawing|poster|after |engraving|Locke|icon|USS|USAF|aircraft|Curtiss|Supermarine|missile", re.I)
PER_CLASS = 11


def get(url, binary=False):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                data = r.read(); return data if binary else json.loads(data)
        except Exception as e:
            print("  retry", attempt, str(e)[:80]); time.sleep(8 * (attempt + 1))
    raise SystemExit("giving up on " + url)


def search(term):
    q = urllib.parse.urlencode({"action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": f"{term} filetype:bitmap", "gsrlimit": 40,
                                "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "format": "json"})
    pages = get(f"{API}?{q}").get("query", {}).get("pages", {}).values()
    for p in pages:
        i = p["imageinfo"][0]; m = i["extmetadata"]; lic = m.get("LicenseShortName", {}).get("value", "")
        if i["mime"] == "image/jpeg" and (lic == "CC0" or lic.startswith("Public domain")) and min(i["width"], i["height"]) >= 400:
            yield {"title": p["title"], "page": i["descriptionurl"], "license": lic, "artist": m.get("Artist", {}).get("value", "")[:120], "url": i["url"]}


out = sys.argv[1]
os.makedirs(out)
sources = []
ONLY = sys.argv[2:] or list(CLASSES)
for cls, terms in CLASSES.items():
    if cls not in ONLY: continue
    got = 0
    for term in terms:
        if got >= PER_CLASS: break
        for r in search(term):
            if got >= PER_CLASS: break
            if BAD.search(r["title"]) or any(s["title"] == r["title"] for s in sources): continue
            try:
                data = get(f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(r['title'][5:])}?width=640", binary=True)
            except SystemExit:
                continue
            name = f"{cls}_{got + 1}.jpg"; open(f"{out}/{name}", "wb").write(data); sources.append({"file": name, "class": cls, **r}); got += 1
            print(name, r["title"], r["license"]); time.sleep(3)
        time.sleep(3)
json.dump(sources, open(f"{out}/sources.json", "w"), indent=1)
