# onnxruntime's network use on Linux and macOS (S-231, D-124)

Run 2 Nov 2026 by `.github/workflows/ort-telemetry.yml` (run 41387435027), onnxruntime 1.31.1 on Python 3.14, GitHub's
`ubuntu-latest` and `macos-latest` (arm64), each with `ORT_DISABLE_TELEMETRY` unset and set to 1. The probe
(`probe.py`) creates a session on a one-node model, runs it 100 times, idles 30 s and exits.

| | Connections seen | How | Network libraries linked by the native module |
|---|---|---|---|
| Linux, default | none | `strace -f -e connect,sendto,sendmsg`, every thread, through exit | none |
| Linux, switch set | none | the same | none |
| macOS, default | none | `lsof` on the process every 0.2 s until exit | CFNetwork and Network frameworks |
| macOS, switch set | none | the same | the same |

Strings in the native module on both: "Failed to create telemetry LogManager", "Error during telemetry flush",
"enable_telemetry_events", "disable_telemetry_events". No Microsoft collector address (`events.data.microsoft.com`) was
found as a plain string.

**Reading it:** no build sent anything in these runs. Linux's module cannot reach the network directly (no networking
library linked). The macOS module links Apple's networking frameworks and carries a telemetry log manager, so it is able
to send; we did not see it do so, with or without the switch. With Windows (`../onnx/results.md`: ETW only, no network
code, 0 connections), this supports D-124: funground-ml sets `ORT_DISABLE_TELEMETRY=1` before importing onnxruntime on
every platform, as Microsoft documents, and the check is rerun when the pinned onnxruntime version changes.

**Limits:** one short run per cell; `lsof` polling can miss a connection shorter than 0.2 s; a send after a longer idle,
or on a schedule, is not ruled out.
