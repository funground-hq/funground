# Spike 18: models evidence for release 0.2 (S-250 YAMNet, S-234 Whisper)

Branch: `cloud/models-evidence` (cloud session, Linux, 4 CPUs). Started 2026-11-05 07:26 UTC; 45-minute budget.
Status: **plan only, work in progress.** Sections are filled in as results arrive.

## Plan

Part 1 (YAMNet, own venv with TensorFlow, 2 CPUs):
1. Fetch Google's YAMNet (TF Hub/Kaggle `google/yamnet`; fall back to tensorflow/models + `yamnet.h5`). Record source, version, SHA-256, licence.
2. ESC-50 clips (evaluation only, not committed) plus edge cases: silence, < 1 window, clipped, quiet.
3. Compare community ONNX (`audiomagic/yamnet-onnx` f25b741) against Google: max score diff, top-1/top-3 agreement, by clip and by window; framing/padding.
4. Convert Google's model with tf2onnx (pinned), twice, check byte-for-byte; compare the same way; size and SHA-256.
5. Learner accuracy on ESC-50 classes that map cleanly to AudioSet names (top-1, top-3).
6. Recommend the file to host; credit for the 521 AudioSet names (CC BY 4.0).

Part 2 (Whisper, own venv with onnxruntime, 2 CPUs):
1. tiny.en q8 (pinned 2575352) and base.en q8 (onnx-community/whisper-base.en, pinned), spike's own decode loop.
2. Speech: CMU ARCTIC incl. ksp (Indian English), LibriSpeech test-clean seeded sample, others if reachable.
3. Conditions: clean, room noise at 20 and 10 dB SNR (seeded), cheap microphone (300 to 3,400 Hz band-pass).
4. WER (normalised) with 95 % bootstrap interval per model, accent, condition; RTF at 1 and 4 threads.
5. 30 most common confusions, grouped.
6. Recommendation tiny.en vs base.en.

Data and models stay in the session scratch area; only scripts, small JSON results and this file are committed.
