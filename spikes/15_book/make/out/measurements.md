## 1. Build time and file size

| Trim | Build, whole process | Of which draw (fonts, pictures, layout) | Print PDF | Screen PDF | Pages |
|---|---|---|---|---|---|
| Square | 8.27 s | 0.86 s | 599 KB | 577 KB | 12 |
| B5 | 8.87 s | 0.91 s | 602 KB | 585 KB | 12 |

Square inside the process (seconds): print_pdf 3.16, screen_pdf 2.92, page_pngs 0.65, spreads 0.22
B5 inside the process (seconds): print_pdf 3.53, screen_pdf 3.01, page_pngs 0.73, spreads 0.26

The four sketches run first, one process each: 2.81 s in all (not in the trim times).

## 2. Grid check

Square: text area 34 lines; canvas side 330 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']
B5: text area 41 lines; canvas side 405 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']

| Trim | Items placed | Vertical positions checked (slot top and bottom, less nudge) | Off the 15 pt line | Result |
|---|---|---|---|---|
| Square | 133 | 264 | 0 | PASS |
| B5 | 133 | 264 | 0 | PASS |

## 3. Longest code line against the measure

| Trim | Longest line, characters | Measure, characters (4 columns less the number gutter, at 9.5 pt) | Result |
|---|---|---|---|
| Square | 30 (f.circle(at="random", size=80)) | 56 | fits |
| B5 | 30 (f.circle(at="random", size=80)) | 44 | fits |

## 4. PDF page boxes (read with pypdf)

| PDF | Pages | Boxes on every page (one line per distinct set) | Fonts in page resources (embedded subsets) |
|---|---|---|---|
| Square print | 12 | MediaBox=[0.0, 0.0, 651.0, 651.0] TrimBox=[25.5, 25.5, 625.5, 625.5] BleedBox=[17.0, 17.0, 634.0, 634.0] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| Square screen | 12 | MediaBox=[0.0, 0.0, 600.0, 600.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| B5 print | 12 | MediaBox=[0.0, 0.0, 550.0, 760.0] TrimBox=[25.5, 25.5, 524.5, 734.5] BleedBox=[17.0, 17.0, 533.0, 743.0] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| B5 screen | 12 | MediaBox=[0.0, 0.0, 499.0, 709.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |

## 5. Script length

| File | Lines |
|---|---|
| build.py | 651 |
| nocoords.py | 87 |
| run_sketch.py | 22 |
| measure.py | 214 |
| sketches/*.py (4 files) | 43 |

## 6. CMYK change of each palette token

Route: `spikes/11_cmyk` option d (littleCMS through Pillow, Windows' RSWOP.icm as the press profile, relative colorimetric with black point compensation). The 11_cmyk scripts print CMYK values only, so the delta-E step (CMYK back to Lab, against the colour's own Lab, CIE76 and CIEDE2000) is added here. The book PDFs themselves are still RGB: this measures what the conversion would do to each token.

| Token (day) | Hex | CMYK % (C/M/Y/K) | dE76 | dE2000 |
|---|---|---|---|---|
| paper (oldlace) | #fdf5e6 | 2/5/13/0 | 5.3 | 3.6 |
| paper-code | #fffaf0 | 2/4/9/0 | 5.9 | 4.7 |
| dot | #e6d8bd | 6/11/25/0 | 6.4 | 3.8 |
| ink (midnightblue) | #191970 | 96/91/7/33 | 21.2 | 8.2 |
| ink-muted | #5a4f7a | 72/71/18/3 | 5.4 | 4.7 |
| tomato | #ff6347 | 0/87/88/0 | 11.4 | 8.6 |
| gold | #ffd700 | 1/11/95/1 | 6.2 | 1.6 |
| hotpink | #ff69b4 | 1/85/3/0 | 13.4 | 9.1 |
| turquoise | #40e0d0 | 75/0/31/0 | 18.2 | 12.3 |
| teal | #008080 | 80/22/39/7 | 6.4 | 3.9 |
| orchid (code keyword) | #9932cc | 55/90/0/0 | 37.8 | 13.0 |
| link / code-string (firebrick) | #b22222 | 16/98/84/7 | 3.5 | 1.9 |
| code-number | #00706b | 80/29/46/16 | 9.7 | 5.2 |
| code-comment | #6b6380 | 58/55/19/9 | 4.1 | 4.1 |

