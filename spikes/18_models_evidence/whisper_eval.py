"""Spike 18 part 2: Whisper word error on accented and degraded speech.

    venv_w/bin/python -I whisper_eval.py MODEL_DIR MANIFEST.jsonl OUT.jsonl --threads 1 [--conds clean,snr20,snr10,mic]

The decode loop is the spike-16 one (../16_models/speech_sounds/whisper_desktop.py: own log-mel, greedy, suppress lists),
copied line for line; only the empty past-key shape is read from config.json so base.en (8 heads) works too.
MANIFEST lines: {"id", "group", "wav", "ref"}. Each clip is degraded per condition with a seed derived from its id.
Appends one json line per (clip, condition) as it goes, so a stopped run keeps its partial results.
"""
import argparse, hashlib, json, os, sys, time
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "16_models", "speech_sounds"))
import onnxruntime as ort
import whisper_desktop as wd

SR = 16000


def fan_noise(n, rng):
    """Room/fan noise: pink-ish noise (1/f by FFT shaping) plus a 100 Hz hum and its harmonics. Seeded."""
    white = rng.standard_normal(n)
    spec = np.fft.rfft(white); f = np.fft.rfftfreq(n, 1 / SR); f[0] = f[1]
    pink = np.fft.irfft(spec / np.sqrt(f), n)
    t = np.arange(n) / SR
    hum = sum(a * np.sin(2 * np.pi * h * t + rng.uniform(0, 6.28)) for h, a in [(100, 1.0), (200, 0.5), (300, 0.25)])
    x = pink / pink.std() + 0.3 * hum / hum.std()
    return x / x.std()


def degrade(audio, cond, seed):
    if cond == "clean": return audio
    if cond == "mic":                                   # cheap microphone: 300 to 3,400 Hz band, 4th-order Butterworth
        sos = butter(4, [300, 3400], btype="band", fs=SR, output="sos")
        return sosfilt(sos, audio).astype(np.float32)
    snr = {"snr20": 20, "snr10": 10}[cond]
    rng = np.random.default_rng(seed)
    noise = fan_noise(len(audio), rng)
    p_sig = np.mean(audio.astype(np.float64) ** 2)
    noise *= np.sqrt(p_sig / (10 ** (snr / 10)))
    y = audio + noise
    return (y / max(1.0, np.abs(y).max())).astype(np.float32)


class W(wd.Whisper):
    def __init__(self, folder, threads):
        so = ort.SessionOptions(); so.intra_op_num_threads = threads; so.inter_op_num_threads = 1
        P = ["CPUExecutionProvider"]
        self.enc = ort.InferenceSession(f"{folder}/onnx/encoder_model_quantized.onnx", so, providers=P)
        self.dec = ort.InferenceSession(f"{folder}/onnx/decoder_model_merged_quantized.onnx", so, providers=P)
        self.tok = wd.Tokenizer.from_file(f"{folder}/tokenizer.json")
        g = json.load(open(f"{folder}/generation_config.json"))
        self.suppress = np.array(g["suppress_tokens"]); self.begin_suppress = g["begin_suppress_tokens"]
        self.past_names = [i.name for i in self.dec.get_inputs() if i.name.startswith("past_key_values")]
        c = json.load(open(f"{folder}/config.json"))
        self.heads, self.hd = c["decoder_attention_heads"], c["d_model"] // c["decoder_attention_heads"]

    def transcribe(self, audio, max_tokens=200):
        """whisper_desktop.Whisper.transcribe line for line; only the empty cache shape (1, heads, 0, head_dim) differs."""
        hidden = self.enc.run(None, {"input_features": wd.log_mel(audio)})[0]
        empty = np.zeros((1, self.heads, 0, self.hd), np.float32)
        past = {n: empty for n in self.past_names}
        ids, out = [wd.SOT, wd.NO_TS], []
        feed_ids, first = np.array([ids], np.int64), True
        outs = [o.name for o in self.dec.get_outputs()][1:]
        for _ in range(max_tokens):
            feeds = {"input_ids": feed_ids, "encoder_hidden_states": hidden, "use_cache_branch": np.array([not first]), **past}
            res = self.dec.run(None, feeds)
            logits = res[0][0, -1].copy()
            logits[self.suppress] = -np.inf
            if not out: logits[self.begin_suppress] = -np.inf
            nxt = int(logits.argmax())
            if nxt == wd.EOS: break
            out.append(nxt)
            for name, value in zip(outs, res[1:]):
                key = name.replace("present", "past_key_values")
                if first or ".decoder." in key: past[key] = value
            feed_ids, first = np.array([[nxt]], np.int64), False
        return self.tok.decode(out).strip()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("manifest"); ap.add_argument("out")
    ap.add_argument("--threads", type=int, default=1); ap.add_argument("--conds", default="clean,snr20,snr10,mic")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    w = W(a.model, a.threads)
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out): r = json.loads(line); done.add((r["id"], r["cond"]))
    items = [json.loads(l) for l in open(a.manifest)]
    if a.limit: items = items[:a.limit]
    with open(a.out, "a") as fo:
        for it in items:
            audio, sr = sf.read(it["wav"], dtype="float32"); assert sr == SR, it
            if audio.ndim > 1: audio = audio.mean(axis=1)
            audio = audio[:30 * SR]
            for cond in a.conds.split(","):
                if (it["id"], cond) in done: continue
                seed = int(hashlib.sha256(f"{it['id']}|{cond}".encode()).hexdigest()[:8], 16)
                x = degrade(audio, cond, seed)
                t = time.perf_counter(); hyp = w.transcribe(x); dt = time.perf_counter() - t
                fo.write(json.dumps({"id": it["id"], "group": it["group"], "cond": cond, "seconds": round(len(x) / SR, 3),
                                     "run_s": round(dt, 4), "threads": a.threads, "ref": it["ref"], "hyp": hyp}) + "\n"); fo.flush()
