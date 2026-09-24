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

## Open

*None.* Next expected: **D-011** — the interactive 2D engine, presented with Spike 07 numbers at the
end of Sprint 2 (story S-035).
