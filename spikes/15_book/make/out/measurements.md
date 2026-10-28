## 1. Build time and file size

| Trim | Build, whole process | Of which draw (fonts, pictures, layout) | Print PDF | Screen PDF | Pages |
|---|---|---|---|---|---|
| Square | 14.13 s | 1.0 s | 556 KB | 527 KB | 12 |
| B5 | 14.45 s | 0.93 s | 556 KB | 536 KB | 12 |

Square inside the process (seconds): print_pdf 5.09, screen_pdf 6.09, page_pngs 1.09, spreads 0.33
B5 inside the process (seconds): print_pdf 4.94, screen_pdf 6.25, page_pngs 1.33, spreads 0.47
Square night: whole process 10.65 s, draw 1.62 s, screen PDF 528 KB; comparison spread 2b 2.8 s.
B5 night: whole process 11.26 s, draw 1.08 s, screen PDF 537 KB; comparison spread 2b 1.87 s.

The sketches run first, one process each: 5.74 s in all (not in the trim times).

## 2. Grid check

Square day: text area 34 lines; canvas side 330 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']
B5 day: text area 41 lines; canvas side 405 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']
Square night: text area 34 lines; canvas side 330 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']
B5 night: text area 41 lines; canvas side 405 pt; optical nudges inside a slot: caption +[1.5], code +[2.5], code number +[3.5], contents +[1.5, 3], folio +[2], label +[3], try this title +[1.5]; exempt: ['full-bleed picture (top at the bleed edge)']

| Trim | Items placed | Vertical positions checked (slot top and bottom, less nudge) | Off the 15 pt line | Result |
|---|---|---|---|---|
| Square day | 138 | 274 | 0 | PASS |
| B5 day | 138 | 274 | 0 | PASS |
| Square night | 138 | 274 | 0 | PASS |
| B5 night | 138 | 274 | 0 | PASS |

## 3. Longest code line against the measure

| Trim | Longest line, characters | Measure, characters (4 columns less the number gutter, at 9.5 pt) | Result |
|---|---|---|---|
| Square | 42 (f.circle(f.random(600), f.random(600), 80)) | 56 | fits |
| B5 | 42 (f.circle(f.random(600), f.random(600), 80)) | 44 | fits |

## 4. PDF page boxes (read with pypdf)

| PDF | Pages | Boxes on every page (one line per distinct set) | Fonts in page resources (embedded subsets) |
|---|---|---|---|
| Square print | 12 | MediaBox=[0.0, 0.0, 651.0, 651.0] TrimBox=[25.5, 25.5, 625.5, 625.5] BleedBox=[17.0, 17.0, 634.0, 634.0] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| Square screen | 12 | MediaBox=[0.0, 0.0, 600.0, 600.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| Square screen_night | 12 | MediaBox=[0.0, 0.0, 600.0, 600.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| B5 print | 12 | MediaBox=[0.0, 0.0, 550.0, 760.0] TrimBox=[25.5, 25.5, 524.5, 734.5] BleedBox=[17.0, 17.0, 533.0, 743.0] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| B5 screen | 12 | MediaBox=[0.0, 0.0, 499.0, 709.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |
| B5 screen_night | 12 | MediaBox=[0.0, 0.0, 499.0, 709.0] TrimBox=[] BleedBox=[] | AtkinsonHyperlegibleNext-Regular-wght400, AtkinsonHyperlegibleNext-Regular-wght700, BricolageGrotesque-96ptExtraBold-wght700, JetBrainsMono-Regular-wght400 |

## 5. Script length

| File | Lines |
|---|---|
| build.py | 879 |
| nocoords.py | 87 |
| run_sketch.py | 19 |
| measure.py | 252 |
| sketches/*.py (5 files, the night comparison included) | 52 |

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

## 7. Text contrast, day theme (WCAG 2.x)

| Text colour | On ground | Ratio | 4.5 needed | Used for |
|---|---|---|---|---|
| #ba4d53 | #fdf5e6 | 4.5 | PASS | code number, contents |
| #9932cc | #fee98a | 4.7 | PASS | code keyword (highlighted) |
| #984595 | #fee98a | 4.8 | PASS | code number, code number (highlighted) |
| #2b739b | #fdf5e6 | 4.8 | PASS | code number |
| #a34999 | #fdf5e6 | 4.9 | PASS | code number |
| #00706b | #fee98a | 4.9 | PASS | code number value (highlighted) |
| #6b6380 | #fdf5e6 | 5.2 | PASS | code comment |
| #9932cc | #fdf5e6 | 5.3 | PASS | code keyword |
| #b22222 | #fee98a | 5.5 | PASS | code string (highlighted) |
| #00706b | #fdf5e6 | 5.5 | PASS | code number value |
| #5a4f7a | #fdd8c6 | 5.6 | PASS | folio, label |
| #5a4f7a | #fdd9dc | 5.7 | PASS | folio |
| #b22222 | #fdf5e6 | 6.2 | PASS | code string |
| #5a4f7a | #d7f1e2 | 6.2 | PASS | folio, label |
| #5a4f7a | #fdefb8 | 6.4 | PASS | folio, label |
| #5a4f7a | #fdf5e6 | 6.8 | PASS | contents, folio, label, side note |
| #191970 | #ffd700 | 10.6 | PASS | try this text, try this title |
| #191970 | #fdd9dc | 11.4 | PASS | predict caption |
| #191970 | #fee98a | 12.2 | PASS | code name (highlighted) |
| #191970 | #fdf5e6 | 13.7 | PASS | caption, chapter title, code name, colophon fonts, contents, heading, prose |

Lowest ratio: 4.5:1 (PASS).

Picture-page grounds (accent mixed 20 per cent with #fdf5e6), and the shade of each accent used for line numbers, tie lines and contents numbers:

| Accent | Hex | Ground tint | Shade for text | Shade on #fdf5e6 |
|---|---|---|---|---|
| tomato | #ff6347 | #fdd8c6 | #ba4d53 | 4.5 |
| gold | #ffd700 | #fdefb8 | #806e3e | 4.6 |
| turquoise | #40e0d0 | #d7f1e2 | #2b739b | 4.8 |
| hotpink | #ff69b4 | #fdd9dc | #a34999 | 4.9 |

## 8. Text contrast, night theme (WCAG 2.x)

| Text colour | On ground | Ratio | 4.5 needed | Used for |
|---|---|---|---|---|
| #ff7ebc | #3e375f | 4.7 | PASS | code number, code number (highlighted) |
| #ee82ee | #3e375f | 4.7 | PASS | code keyword (highlighted) |
| #ff6347 | #191970 | 5.0 | PASS | code number, contents |
| #ffa07a | #3e375f | 5.5 | PASS | code string (highlighted) |
| #c4c0e6 | #214183 | 5.6 | PASS | folio, label |
| #ff69b4 | #191970 | 5.6 | PASS | code number |
| #c4c0e6 | #473f5a | 5.7 | PASS | folio, label |
| #a9a4d6 | #191970 | 6.3 | PASS | code comment |
| #c4c0e6 | #47297e | 6.4 | PASS | folio |
| #ee82ee | #191970 | 6.4 | PASS | code keyword |
| #40e0d0 | #3e375f | 6.7 | PASS | code number value (highlighted) |
| #c4c0e6 | #472868 | 6.8 | PASS | folio, label |
| #ffa07a | #191970 | 7.5 | PASS | code string |
| #c4c0e6 | #191970 | 8.5 | PASS | contents, folio, label, side note |
| #40e0d0 | #191970 | 9.0 | PASS | code number, code number value |
| #fdf5e6 | #3e375f | 10.1 | PASS | code name (highlighted) |
| #fdf5e6 | #47297e | 10.3 | PASS | predict caption |
| #191970 | #ffd700 | 10.6 | PASS | try this text, try this title |
| #fdf5e6 | #191970 | 13.7 | PASS | caption, chapter title, code name, colophon fonts, contents, heading, prose |

Lowest ratio: 4.7:1 (PASS).

Picture-page grounds (accent mixed 20 per cent with #191970), and the shade of each accent used for line numbers, tie lines and contents numbers:

| Accent | Hex | Ground tint | Shade for text | Shade on #191970 |
|---|---|---|---|---|
| tomato | #ff6347 | #472868 | #ff6347 | 5.0 |
| gold | #ffd700 | #473f5a | #ffd700 | 10.6 |
| turquoise | #40e0d0 | #214183 | #40e0d0 | 9.0 |
| hotpink | #ff69b4 | #47297e | #ff69b4 | 5.6 |

