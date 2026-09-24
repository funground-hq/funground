# Decision log

Every decision the maintainer has been asked to make, in the order asked. One row per decision;
the full reasoning lives in the linked ADR, contract row or sprint document. Status: `pending` ·
`accepted` · `rejected` · `superseded by D-nnn`. See `docs/PROCESS.md` § Decisions for how entries
are raised and closed.

| ID | Date asked | Decision | Options offered | Recommended | Outcome | Decided | Where it lives |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-09-24 | Which library renders 2D (first rasteriser) | A two peer renderers · B Skia · C Cairo · D pygame-only base | C Cairo | **accepted** — topology: Playground owns semantics + IR, pygame-ce is platform + presentation, renderers are IR consumers. *Engine clause (Cairo as default) superseded by D-010.* | 2026-09-24 | `ADR-001` |
| D-002 | 2026-09-24 | Angle unit for `rotate()` | degrees · radians | degrees + `p.radians()` / `p.degrees()` | **accepted** | 2026-09-24 | `Semantic_Contract.md` F1 |
| D-003 | 2026-09-24 | Honour RGBA alpha (v0.5 silently drops it) | honour · keep dropping | honour | **accepted** — applies when the vector renderer lands (Sprint 3), goldens regenerated once | 2026-09-24 | `Semantic_Contract.md` S2 |
| D-004 | 2026-09-24 | Stroke alignment | inside the shape (v0.5) · centred on the edge (vector norm) | centred | **accepted** — applies in Sprint 3 with D-003/D-005 | 2026-09-24 | `Semantic_Contract.md` S4 |
| D-005 | 2026-09-24 | Fractional coordinates and anti-aliasing | round to whole pixels, hard edges (v0.5) · honour fractions, anti-alias | honour + AA | **accepted** — applies in Sprint 3 | 2026-09-24 | `Semantic_Contract.md` C6 |
| D-006 | 2026-09-24 | Default-font mechanism and font | OS font by name · install bundled font into OS · text as glyph outlines via fontTools + uharfbuzz in the IR · larger text stack (pango / Skia) | run Spike 06 on the outlines route, then bundle an OFL font | **accepted** — mechanism validated by Spike 06; font file = D-009. Known limitation accepted: PDFs carry outlines, not searchable text, until fonts are embedded (S-032) | 2026-09-24 | `Semantic_Contract.md` T2; `Text_Subsystem_Note.md` |
| D-007 | 2026-09-24 | Phase 1 boundary and checkpoints | one phase, one checkpoint · Phase 1 = Sprints 1–3 with three golden-verified checkpoints | three checkpoints | **accepted** | 2026-09-24 | `PROCESS.md` phases table; backlog |
| D-008 | 2026-09-24 | Fate of pygame drawing code after the vector renderer | keep as permanent fallback renderer · name `LegacyPygameRenderer`, delete in Sprint 3 | delete | **accepted** | 2026-09-24 | story S-019 / S-026 |
| D-009 | 2026-09-24 | Which font file to bundle as Playground's default (closes D-006) | A DejaVu Sans (Bitstream Vera licence, 757 KB, widest coverage) · B Noto Sans (OFL, 2 MB or instanced) · C Source Sans 3 (OFL, 431 KB, no `fi`) | A | **accepted — DejaVu Sans.** Licence is Bitstream Vera + public domain (permissive, not OFL); ship `DejaVu-LICENSE.txt` with the font | 2026-09-24 | Spike 06, `spikes/RESULTS.md` §6; `Semantic_Contract.md` T2 |
| D-010 | 2026-09-24 | Reopen the interactive-renderer engine choice pending a broader bake-off? | A keep ADR-001 · B reopen, Cairo = reference implementation, Spike 07 in Sprint 2, decide D-011 before Sprint 3 · C as B without Blend2D | B | **accepted — B.** Providers are selected per capability and workload, not per framework | 2026-09-24 | `ADR-002` |

| D-011 | 2026-09-25 | Which engine renders interactive frames in Sprint 3 (closes ADR-002's open clause) | A Cairo · B Blend2D · C Skia · D Cairo now, Blend2D as an optional fast renderer once its binding passes the gate | D | **pending** | | Spike 07, `spikes/RESULTS.md` §7 |

## Open

### D-011 — the interactive 2D engine

**Context.** ADR-002 left the engine open pending a bake-off. Spike 07 fed the real Sprint-2 IR to
Cairo, Skia and Blend2D. Sprint 3 needs the answer: it implements the first vector renderer, applies
contract changes D-003/4/5, regenerates goldens once and deletes the legacy renderer. The IR is
proven neutral (three engines, identical pixels), so this decision is *reversible at renderer-file
cost* — but the goldens and the base-install dependency set follow from it.

**Options.**

| | A. Cairo | B. Blend2D | C. Skia | D. Cairo now + Blend2D later (optional) |
|---|---|---|---|---|
| Runs the whole IR today | ✅ | **✗** no clip, no matrix, no fill rule in the binding | ✅ | ✅ (Cairo) |
| Speed, scene A / C @ 640×400 | 70 / 21 ms | **24 / 5.5 ms** | 206 / 506 ms | Cairo now; 3–10× faster later |
| Install | 2.0 MB, 1.6 s | 2.2 MB, 1.3 s (+ Cairo for export) | 81 MB, 18 s | 2 MB; +2 MB extra |
| PDF / SVG | native | needs Cairo alongside | native | Cairo |
| Platforms | all | no macOS x86_64 | all | all (extra where wheels exist) |
| Binding risk | low | medium–high (2025, one company, incomplete) | low | low now; gated later |
| Text | outlines route (IR) | outlines route + optional native | outlines route | outlines route |

**Trade-offs.** A is complete, small, mature and exports natively; it is the slowest of the *correct*
engines, but at teaching scale (a few hundred shapes) it holds 60 fps at 640×400 and ~40 fps at
720p. B is the fastest by far and tiny, but its binding cannot clip — a core IR op — and cannot be
relied on for macOS Intel or long-term ownership; choosing it now means either forgoing clipping
or writing and owning a C++ binding. C is complete but unacceptable as a classroom base install
(81 MB, slowest on CPU). D takes A's certainty for Sprint 3 and keeps B's upside: when `blend2d-py`
exposes clipping and a matrix (or we decide to own a binding), it slots in as a second IR consumer
behind `playground[fast]`, with Cairo retained for export — exactly the per-capability provider
model the maintainer accepted in D-010.

**Recommendation: D.** Cairo is the Sprint 3 renderer and the export path; Blend2D is tracked as a
gated optional renderer (new story), with Spike 07 re-run when its binding changes. **Why:** every
Sprint-3 goal is met by Cairo with low risk; the only thing Blend2D adds today is speed we do not
yet need, at a risk we should not take for a teaching default; and the IR makes adding it later a
~100-line file, as this spike demonstrated.

**What would change it:** a `blend2d-py` release with clip/matrix/fill-rule and macOS x86_64 wheels
(then B becomes a serious default candidate); or a decision that classroom sketches must sustain
thousands of translucent shapes at 60 fps.
