# Decision log

Every decision the maintainer has been asked to make, in the order asked. One row per decision;
the full reasoning lives in the linked ADR, contract row or sprint document. Status: `pending` ·
`accepted` · `rejected` · `superseded by D-nnn`. See `docs/PROCESS.md` § Decisions for how entries
are raised and closed.

| ID | Date asked | Decision | Options offered | Recommended | Outcome | Decided | Where it lives |
|---|---|---|---|---|---|---|---|
| D-001 | 2026-09-24 | Which library renders 2D (first rasteriser) | A two peer renderers · B Skia · C Cairo · D pygame-only base | C Cairo | **accepted** — Cairo is the default 2D renderer; pygame-ce is platform + presentation only; Skia/GPU are future IR consumers | 2026-09-24 | `ADR-001` |
| D-002 | 2026-09-24 | Angle unit for `rotate()` | degrees · radians | degrees + `p.radians()` / `p.degrees()` | **accepted** | 2026-09-24 | `Semantic_Contract.md` F1 |
| D-003 | 2026-09-24 | Honour RGBA alpha (v0.5 silently drops it) | honour · keep dropping | honour | **accepted** — applies when Cairo lands (Sprint 3), goldens regenerated once | 2026-09-24 | `Semantic_Contract.md` S2 |
| D-004 | 2026-09-24 | Stroke alignment | inside the shape (v0.5) · centred on the edge (vector norm) | centred | **accepted** — applies in Sprint 3 with D-003/D-005 | 2026-09-24 | `Semantic_Contract.md` S4 |
| D-005 | 2026-09-24 | Fractional coordinates and anti-aliasing | round to whole pixels, hard edges (v0.5) · honour fractions, anti-alias | honour + AA | **accepted** — applies in Sprint 3 | 2026-09-24 | `Semantic_Contract.md` C6 |
| D-006 | 2026-09-24 | Default-font mechanism and font | OS font by name · install bundled font into OS · text as glyph outlines via fontTools + uharfbuzz in the IR · larger text stack (pango / Skia) | run Spike 06 on the outlines route, then bundle an OFL font | **accepted** — mechanism decided in principle, font file chosen after Spike 06. Known limitation accepted: PDFs will contain outlines, not searchable text, until fonts are embedded (backlog S-032) | 2026-09-24 | `Semantic_Contract.md` T2; story S-031 |
| D-007 | 2026-09-24 | Phase 1 boundary and checkpoints | one phase, one checkpoint · Phase 1 = Sprints 1–3 with three golden-verified checkpoints | three checkpoints | **accepted** | 2026-09-24 | `PROCESS.md` phases table; backlog |
| D-008 | 2026-09-24 | Fate of pygame drawing code after Cairo | keep as permanent fallback renderer · name `LegacyPygameRenderer`, delete in Sprint 3 | delete | **accepted** | 2026-09-24 | story S-019 / S-026 |

| D-009 | 2026-09-24 | Which font file to bundle as Playground's default (closes D-006) | see below | DejaVu Sans | **pending** | | Spike 06, `spikes/RESULTS.md` §6 |
| D-010 | 2026-09-24 | Reopen the interactive-renderer engine choice (Cairo) pending a broader bake-off? | A keep ADR-001 · B reopen, Cairo = reference implementation, Spike 07 in Sprint 2, decide D-011 before Sprint 3 · C as B without Blend2D | B | **pending** | | `ADR-002` |

## Open

### D-010 — reopen the renderer engine choice

**Context.** The maintainer asked whether Cairo is the right long-term bet given that browser engines
have moved to Skia/GPU renderers. ADR-001 was decided on one spike (Cairo vs Skia, one scene). The
IR is what protects us from a wrong engine choice, and Sprint 2 builds the IR without depending on
the engine — so this is the cheapest moment to widen the evidence. Not deciding means Sprint 3 starts
implementing Cairo on ADR-001 as written.

**Options and trade-offs.** In `ADR-002` (A keep / B reopen with bake-off incl. Blend2D behind a
binding-coverage gate / C reopen, Cairo vs Skia only). Schedule cost of B and C: none for Sprint 2;
one bounded spike (~1–2 days) in parallel. Risk of A: an engine decision taken on thin evidence and
revisited after Cairo-specific code exists.

**Recommendation: B.** **Why:** it answers the concern with data instead of argument; a third IR
consumer is the strongest test of backend-neutrality we can buy; and the binding-coverage gate keeps
Blend2D honest — today's `blend2d-py` exposes no clipping or scale, so it cannot run the IR without
either an upstream release or a binding we would own.

**What would change it:** if Sprint 3 had already started (it hasn't), or if the maintainer wants the
smallest possible dependency set decided now rather than measured.

### D-009 — the bundled default font

**Context.** Spike 06 (S-031) confirmed the outlines route works for every candidate: deterministic,
0.44–0.48 ms per line cached, correct kerning/ligatures/Devanagari. What remains is *which* file ships
inside the package. It sets the look of every `p.text()` call, the install size, and which scripts
learners can write in without adding a font. Not making it blocks S-029 (text subsystem v1) but
nothing in Sprint 2.

**Options.**

| | A. DejaVu Sans | B. Noto Sans | C. Source Sans 3 |
|---|---|---|---|
| Licence | Bitstream Vera + public-domain additions — free to bundle and redistribute; **not** SIL OFL | SIL OFL 1.1 | SIL OFL 1.1 |
| Size in package | 757 KB | 2.0 MB as shipped (variable); ~600 KB after instancing to Regular with fontTools (an extra build step) | 431 KB |
| Script coverage (6253 / 4515 / 2478 glyphs) | Latin, Greek, Cyrillic, Armenian, Georgian, Arabic (partial), Lao, symbols, maths, box drawing | Latin, Greek, Cyrillic | Latin, Greek, Cyrillic |
| `fi` ligature by default | ✅ | ✅ | ✗ (5 glyphs) |
| Look | Wide, neutral, very familiar (matplotlib's default font) | Modern humanist, polished | Narrower, typographically refined |
| Small-size legibility (12 px, unhinted) | good | good | good |
| Devanagari / other complex scripts | ✗ for all three — add Noto per-script fonts later (642 KB each) | | |

**Trade-offs.** A gives the most learner-relevant coverage per byte and a look most instructors will
already recognise, at the cost of not being OFL (the licence is equally permissive for bundling;
it is simply a different text). B is OFL and the most polished but is the largest and needs an
instancing step in the build. C is OFL and smallest but has the narrowest glyph set and no default
`fi` ligature, so `office` renders as five glyphs.

**Recommendation: A, DejaVu Sans.** Coverage per byte and familiarity matter most for a teaching
default; the licence difference is a formality (record it in `docs/design/` and ship the licence
file). Choose B if you want "OFL" to be literally true; C is not worth its size saving.

**What would change it:** a requirement that every bundled asset be OFL specifically; or a need for
CJK/Devanagari out of the box, which none of the three provides and would be a separate font anyway.
