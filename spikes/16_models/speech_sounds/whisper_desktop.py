"""S-231 speech: Whisper tiny.en q8 on onnxruntime, our own log-mel and greedy decode loop (desktop).

    mlvenv python whisper_desktop.py MODEL_DIR WAV16K [WAV16K ...]   -> one json line per clip

MODEL_DIR holds onnx/encoder_model_quantized.onnx, onnx/decoder_model_merged_quantized.onnx, tokenizer.json,
generation_config.json. Wavs are 16 kHz mono (made by prep_audio.py).
"""
import json, os, sys, time
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
import numpy as np
import onnxruntime as ort
import soundfile as sf
from tokenizers import Tokenizer

SR, N_FFT, HOP, N_MELS, CHUNK = 16000, 400, 160, 80, 30 * 16000
SOT, NO_TS, EOS = 50257, 50362, 50256


def mel_filters():
    """Slaney mel filterbank (what librosa and Whisper use), shape (80, 201)."""
    def hz2mel(f): f = np.asarray(f, float); return np.where(f < 1000, f / (200 / 3), 15 + np.log(np.maximum(f, 1e-9) / 1000) / (np.log(6.4) / 27))
    def mel2hz(m): m = np.asarray(m, float); return np.where(m < 15, m * (200 / 3), 1000 * np.exp((np.log(6.4) / 27) * (m - 15)))
    freqs = np.linspace(0, SR / 2, N_FFT // 2 + 1)
    pts = mel2hz(np.linspace(hz2mel(0), hz2mel(SR / 2), N_MELS + 2))
    d = np.diff(pts)
    ramps = pts[:, None] - freqs[None, :]
    w = np.maximum(0, np.minimum(-ramps[:-2] / d[:-1, None], ramps[2:] / d[1:, None]))
    return (w * (2.0 / (pts[2:N_MELS + 2] - pts[:N_MELS]))[:, None]).astype(np.float32)


FILTERS = mel_filters()


def log_mel(audio):
    x = np.zeros(CHUNK, np.float32); x[:min(len(audio), CHUNK)] = audio[:CHUNK]
    x = np.pad(x, N_FFT // 2, mode="reflect")
    frames = np.lib.stride_tricks.sliding_window_view(x, N_FFT)[::HOP][:-1]
    win = np.hanning(N_FFT + 1)[:-1].astype(np.float32)
    mag = np.abs(np.fft.rfft(frames * win, axis=1)) ** 2
    mel = FILTERS @ mag.T
    log = np.log10(np.maximum(mel, 1e-10))
    log = np.maximum(log, log.max() - 8.0)
    return ((log + 4.0) / 4.0).astype(np.float32)[None]


class Whisper:
    def __init__(self, folder):
        so = ort.SessionOptions()
        self.enc = ort.InferenceSession(f"{folder}/onnx/encoder_model_quantized.onnx", so, providers=["CPUExecutionProvider"])
        self.dec = ort.InferenceSession(f"{folder}/onnx/decoder_model_merged_quantized.onnx", so, providers=["CPUExecutionProvider"])
        self.tok = Tokenizer.from_file(f"{folder}/tokenizer.json")
        g = json.load(open(f"{folder}/generation_config.json"))
        self.suppress = np.array(g["suppress_tokens"]); self.begin_suppress = g["begin_suppress_tokens"]
        self.past_names = [i.name for i in self.dec.get_inputs() if i.name.startswith("past_key_values")]

    def transcribe(self, audio, max_tokens=200):
        hidden = self.enc.run(None, {"input_features": log_mel(audio)})[0]
        empty = np.zeros((1, 6, 0, 64), np.float32)
        past = {n: empty for n in self.past_names}
        ids, out = [SOT, NO_TS], []
        feed_ids, first = np.array([ids], np.int64), True
        for _ in range(max_tokens):
            feeds = {"input_ids": feed_ids, "encoder_hidden_states": hidden, "use_cache_branch": np.array([not first]), **past}
            res = self.dec.run(None, feeds)
            logits = res[0][0, -1].copy()
            logits[self.suppress] = -np.inf
            if not out: logits[self.begin_suppress] = -np.inf
            nxt = int(logits.argmax())
            if nxt == EOS: break
            out.append(nxt)
            for name, value in zip([o.name for o in self.dec.get_outputs()][1:], res[1:]):
                key = name.replace("present", "past_key_values")
                if first or ".decoder." in key: past[key] = value          # encoder k/v are computed once
            feed_ids, first = np.array([[nxt]], np.int64), False
        return self.tok.decode(out).strip()


if __name__ == "__main__":
    t0 = time.perf_counter(); w = Whisper(sys.argv[1]); load_s = time.perf_counter() - t0
    for path in sys.argv[2:]:
        audio, sr = sf.read(path, dtype="float32"); assert sr == SR
        runs = []
        for _ in range(3):
            t = time.perf_counter(); text = w.transcribe(audio); runs.append(time.perf_counter() - t)
        print(json.dumps({"clip": os.path.basename(path), "seconds": len(audio) / SR, "load_s": round(load_s, 2), "run_s": [round(r, 3) for r in runs],
                          "rtf": round(min(runs) / (len(audio) / SR), 3), "rtf_first": round(runs[0] / (len(audio) / SR), 3), "text": text}))
