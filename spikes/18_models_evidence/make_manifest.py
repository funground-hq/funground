"""Spike 18: seeded speech manifests.  make_manifest.py ARCTIC_DIR LIBRI_DIR OUT_DIR  (seed 18)
ARCTIC: per speaker a seeded sample (ksp 200, others 60) of utterances. LibriSpeech test-clean: seeded 500 utterances."""
import glob, json, os, random, re, sys
arctic, libri, out = sys.argv[1:4]
rng = random.Random(18)
GROUP = {"ksp": "indian", "bdl": "us", "slt": "us", "jmk": "canadian", "awb": "scottish"}
N = {"ksp": 200}
items = []
for spk, grp in GROUP.items():
    d = glob.glob(f"{arctic}/{spk}/cmu_us_{spk}_arctic")[0]
    txt = dict(re.findall(r'\( (\S+) "(.*)" \)', open(f"{d}/etc/txt.done.data").read()))
    ids = sorted(txt); rng.shuffle(ids)
    for u in sorted(ids[:N.get(spk, 60)]):
        items.append({"id": f"arctic_{spk}_{u}", "group": grp, "wav": f"{d}/wav/{u}.wav", "ref": txt[u]})
json.dump(None, open(os.devnull, "w"))
random.Random(180).shuffle(items)  # mixed order: a run stopped early still covers every speaker
with open(f"{out}/arctic.jsonl", "w") as f:
    for it in items: f.write(json.dumps(it) + "\n")
if os.path.isdir(libri):
    li = []
    for t in sorted(glob.glob(f"{libri}/**/*.trans.txt", recursive=True)):
        for line in open(t):
            k, ref = line.strip().split(" ", 1)
            li.append({"id": f"libri_{k}", "group": "librispeech", "wav": os.path.join(os.path.dirname(t), k + ".flac"), "ref": ref})
    rng2 = random.Random(18); rng2.shuffle(li)
    with open(f"{out}/libri.jsonl", "w") as f:
        for it in li[:500]: f.write(json.dumps(it) + "\n")
print(len(items))
