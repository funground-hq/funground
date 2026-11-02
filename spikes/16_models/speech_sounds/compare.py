"""Word error rate (Whisper, both platforms) and desktop-against-web score differences (YAMNet). Run from this folder:
    compare.py > compare.json     (reads whisper_desktop.jsonl, web_whisper.json, yamnet_desktop.jsonl, web_yamnet.json)"""
import json, re

REF = {"tts": "Draw a red circle in the middle of the screen, then make it bounce off the walls and change color every time it hits one.",
       "gettysburg": "This is a LibriVox recording. All LibriVox recordings are in the public domain. For more information or to volunteer, please visit LibriVox.org."}


def words(s): return re.sub(r"[^a-z0-9' ]", " ", s.lower()).split()


def wer(ref, hyp):
    r, h = words(ref), words(hyp); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
    return d[len(h)] / len(r)


out = {"whisper": {}, "yamnet": {}}
desk = {j["clip"].split(".")[0]: j for j in map(json.loads, open("whisper_desktop.jsonl"))}
web = json.load(open("web_whisper.json"))["result"]["clips"]
for k in REF:
    out["whisper"][k] = {"desktop_text": desk[k]["text"], "web_text": web[k]["text"], "wer_desktop": round(wer(REF[k], desk[k]["text"]), 3), "wer_web": round(wer(REF[k], web[k]["text"]), 3),
                         "same_words_desktop_web": words(desk[k]["text"]) == words(web[k]["text"]), "exact_same_string": desk[k]["text"] == web[k]["text"],
                         "rtf_desktop": desk[k]["rtf"], "rtf_web": round(web[k]["rtf"], 3)}
dy = {j["clip"].split(".")[0]: j for j in map(json.loads, open("yamnet_desktop.jsonl"))}
wy = json.load(open("web_yamnet.json"))["result"]["clips"]
for k in dy:
    diff = max(abs(a - b) for a, b in zip(dy[k]["mean"], wy[k]["scores"]))
    out["yamnet"][k] = {"max_abs_score_diff": round(diff, 5), "top3_desktop": dy[k]["top3"], "top3_web": wy[k]["top"], "ms_single_window_desktop": dy[k]["ms_single_window_call"],
                        "ms_single_window_web": round(wy[k]["ms_single_window_call"], 1), "ms_per_window_in_clip_desktop": dy[k]["ms_per_window_in_clip"], "ms_per_window_in_clip_web": round(wy[k]["ms_per_window"], 1)}
print(json.dumps(out, indent=1))
