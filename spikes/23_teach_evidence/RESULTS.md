# S-235 evidence: teach and guess from a few camera pictures

2026-11-05, 07:42 to 07:48 UTC. Branch: `cloud/teach-evidence` (the name asked for). Nothing in `funground/` or `ml/` changed.

Files: `embed.py` (pictures to vectors), `analyse.py` (all the splits), `results.json` (every number below).

## Set-up and what was measured

- **Model:** DINOv2-small q8, `https://huggingface.co/onnx-community/dinov2-small/resolve/main/onnx/model_quantized.onnx`,
  24,446,700 bytes, SHA-256 `c179f8f7f592449c4c1bca4cd124a7538021428c5ffb89afde9503935b197efb` (downloaded 2026-11-05).
  The earlier results (`spikes/16_models/onnx/results.md`, `.../speech_sounds/results.md`) give the size (24.4 MB) but **no hash
  or commit**, so I could not check this was the identical file. The size matches. It is the CLS token, L2-normalised, with the same
  preprocessing as `knn_teach.py`.
- **Data:** Rock Paper Scissors (`https://storage.googleapis.com/download.tensorflow.org/data/rps.zip`, 200,682,221 bytes, 2,520 PNGs,
  not in git). From it, 500 per class were drawn (seed 0), 1,500 in all. **Only 3 classes**, so "4 and 5 classes" could not be run.
  **These are computer-rendered hands on a white background**, not real camera photos (see "How far this reaches").
- **Embedding:** 4 processes, onnxruntime 1.29.0 at 1 thread each, numpy 2.5.3, Pillow 12.3.0, Python 3 (system), `ORT_DISABLE_TELEMETRY=1`.
  1,500 pictures took **86.8 s** wall clock (about 17 pictures/s on 4 CPUs). The vectors are in the scratchpad, not in git.
- **Splits:** `analyse.py <prefix> results.json 2000`, numpy `default_rng(235)`. Each setting has **2,000 random splits**. Each split
  draws the classes, then n taught pictures per class, then 60 untaught test pictures per class. kNN uses cosine similarity. With k=3
  the 3 nearest pictures vote and a tie goes to the nearest. "How sure" (the margin) = the best class's top similarity minus the
  runner-up class's top similarity.
- **What "95 %" means:** "mean 95" is the 95 % interval of the mean over the 2,000 splits. "Learner's range" is the 2.5th to 97.5th
  percentile of single splits: what one learner might actually see.

## 2. Accuracy (per test picture, averaged over 2,000 splits)

| Classes | n per class | k=1 mean (95 % of mean) | k=1 learner's range | k=3 mean | k=3 learner's range |
|---|---|---|---|---|---|
| 2 | 1 | 68.3 % (67.8–68.8) | 49–89 % | 68.3 % (same as k=1: only 2 pictures taught) | 49–89 % |
| 2 | 2 | 74.5 % (74.1–75.0) | 54–93 % | 66.4 % | 50–86 % |
| 2 | 3 | 79.4 % (79.0–79.8) | 60–95 % | 72.7 % | 53–90 % |
| 2 | 5 | 84.4 % (84.1–84.7) | 68–97 % | 78.9 % | 61–93 % |
| 2 | 10 | 92.0 % (91.8–92.2) | 80–99 % | 87.0 % | 73–98 % |
| 2 | 20 | 97.2 % (97.0–97.3) | 90–100 % | 94.3 % | 85–100 % |
| 3 | 1 | 53.8 % (53.4–54.2) | 38–71 % | 53.8 % | 38–71 % |
| 3 | 2 | 61.8 % (61.4–62.1) | 46–77 % | 56.3 % | 42–72 % |
| 3 | 3 | 66.9 % (66.6–67.3) | 51–81 % | 61.1 % | 46–76 % |
| 3 | 5 | 75.2 % (74.9–75.5) | 62–87 % | 68.0 % | 55–81 % |
| 3 | 10 | 86.2 % (86.0–86.4) | 76–95 % | 78.7 % | 67–89 % |
| 3 | 20 | 94.9 % (94.8–95.1) | 88–99 % | 90.1 % | 82–97 % |

**k=1 beats k=3 in every setting** by 5 to 8 points. This task is much harder than S-231's cat/dog/bird (91 % with 3 per class):
three hand shapes on the same white background look alike to DINOv2. Top similarities run from 0.83 to 0.98 for *every* picture.

## 3. Is "how sure" honest?

Pooled over all 12 settings above, the mapping was fitted on the even-numbered splits and tested on the odd ones (k=1 shown;
k=3 is in `results.json`).

| Margin | Test pictures | How often right | Proposal A score |
|---|---|---|---|
| 0–0.01 | 223,197 | 51.7 % | 0.53 |
| 0.01–0.02 | 221,748 | 63.0 % | 0.60 |
| 0.02–0.05 | 628,840 | 78.2 % | 0.73 |
| 0.05–0.1 | 534,859 | 87.3 % | 0.94 |
| 0.1–0.15 | 143,136 | 89.5 % | 1.00 |
| 0.15–0.2 | 36,253 | 90.3 % | 1.00 |
| 0.2–0.3 | 11,448 | 91.8 % | 1.00 |
| 0.3–0.4 | 508 | 95.3 % | 1.00 |

- The **raw margin is not an honest 0-to-1 number**. Its values are tiny (most are under 0.1), yet a margin of 0.05 is already right
  about 85 % of the time. The calibration error (ECE: the average gap between the score and how often it is right, in 10 bins) is
  **0.72**.
- The margin *does* rank the guesses well: the bigger the margin, the more often the guess is right, without exception. So it is
  useful, just on the wrong scale.
- **Proposal A (plain):** `score = 0.5 + 0.5 * min(1, margin / M)`. A margin of 0 means a coin toss between the top two classes.
  The fitted M is **0.075** for k=1 (0.105 for k=3). Its ECE on the test splits is **0.051** (k=1) and 0.044 (k=3).
  - Its weak spot: from a margin of about 0.1 it gives 1.0, while the truth is only 0.89 to 0.95. A cap such as 0.95 would be more
    honest. That is a suggestion, not measured.
- **Proposal B (logistic):** `1 / (1 + exp(-(0.335 + 20.6 * margin)))` for k=1. Its ECE on the test splits is 0.041 (k=1) and 0.027 (k=3).
  It is a little better than A but harder to explain.
- **Neither mapping holds across every setting:**

| Setting | ECE, A | ECE, B | How often right overall |
|---|---|---|---|
| 2 classes, n=1 | 0.159 | 0.135 | 68 % |
| 3 classes, n=1 | 0.226 | 0.219 | 54 % |
| 2 classes, n=3 / n=5 | 0.038 / 0.052 | 0.025 / 0.059 | 79 % / 84 % |
| 3 classes, n=3 / n=5 | 0.068 / 0.039 | 0.069 / 0.054 | 67 % / 75 % |
| 2 classes, n=20 | 0.125 | 0.165 | 97 % |
| 3 classes, n=20 | 0.187 | 0.196 | 95 % |

  With 1 example the score is **over-confident**. With 20 it is **under-confident**, because more examples raise accuracy but do not
  widen the margins. A mapping that also knew n (the number taught) would fix this. I did not try one.

## 4. Something it was never taught

Two classes were taught with k=1, and pictures of the third were shown. The left-out class rotated through the splits (2,000 splits,
60 unknown pictures each).

- **The unknown pictures look just like taught ones.** With n=5, the median top similarity is 0.914 for unknown pictures and 0.944 for
  known ones. The median margin is 0.041 for unknown and 0.051 for known. **6.9 % of unknown pictures get a margin above 0.1**: to
  proposal A, that is a confident "100 %" for a class the picture does not belong to.
- A "does not know" rule *top similarity < T* (n=5; n=3 and n=10 are in `results.json`):

| T | Unknown pictures caught | Right answers lost (share of all known pictures) | Wrong answers caught |
|---|---|---|---|
| 0.85 | 9 % | 2.7 % | 1.5 % |
| 0.90 | 34 % | 10.2 % | 5.1 % |
| 0.92 | 58 % | 18.7 % | 8.1 % |
| 0.94 | 84 % | 34.1 % | 11.7 % |

  On this data no threshold is cheap. Catching half the unknown pictures costs about one right answer in five. The threshold also
  depends on the data: these similarities are all high because every picture shares a white background. On real photos the numbers
  would be quite different (unverified).

## 5. Bad teaching

- **1 of 5 examples labelled wrongly**: 3 classes, 5 per class, and in each class one example was given another class's label. Both k
  were measured on the same 2,000 splits:
  - k=1 falls from 74.9 % (clean) to **62.3 %** (95 % of mean 62.0–62.6).
  - k=3 falls from 68.0 % to **60.8 %** (60.5–61.1).
  - k=3 loses less (7 points against 12.6) but still ends below k=1.
- **20 examples against 3**: 2 classes, 2,000 splits.
  - k=1: the class with 20 is right 99.1 % of the time, the class with 3 **60.6 %**.
  - k=3: 99.5 % and **34.5 %**. The class with 3 is crushed (one learner in 40 sees under 2 %).
  - So **k=1 copes far better** with uneven teaching.

## Recommendation (proposals for the maintainer)

1. **Fewest examples: tell a learner "at least 5 of each, 10 is better".** On this data, with 2 classes, 5 per class gives 84 % and
   10 gives 92 %. With 3 per class it is 79 %, and one learner in 40 gets 60 % or worse. ml.guess could warn while a class has fewer
   than 5.
2. **Default k = 1.** It is better in every clean setting and much better when the classes are uneven. k=3 only damps label noise a
   little, and still ends lower. If k=3 is offered, it should vote by class with each class's count balanced, which was not tested here.
3. **`.score`:** `0.5 + 0.5 * min(1, margin / 0.075)`, with an upper cap of about 0.95 (the cap is a proposal, not measured).
   - Write the meaning as "1 means it is fairly sure, 0.5 means it is guessing between two". **Do not** promise "0.8 means right 8
     times in 10": it is over-confident when there are few examples and under-confident when there are many.
   - Show the raw margin too, for the curious.
   - The constant 0.075 comes from one dataset, so it should be re-fitted on real photos before it goes into the contract.
4. **Do not offer a "does not know" answer by default.** On this data the score cannot tell "never taught" from "taught", and a
   threshold costs a fifth of the right answers to catch half the unknown pictures.
   - Better teaching: tell learners to add a "nothing / something else" class with its own examples. This is the honest way to say
     "none of these".
   - Re-test the "does not know" question on real photos before deciding.

**How far this reaches.** One dataset, 3 classes, computer-rendered hands on plain white backgrounds. A real learner's camera adds
changing light, clutter and the same room behind every class, so absolute accuracy and the similarity threshold here should not be
copied into the contract. What should carry over, because it follows from how kNN works and not from these pictures:

- k=1 beats k=3 for small and uneven teaching sets.
- The raw margin ranks guesses well but is on the wrong scale.
- With 1 to 3 examples a learner sees big swings from one teaching set to the next.

Not done: 4 and 5 classes (the data has 3), Imagenette, real webcam photos, and checking the model file against a pinned hash.

## For the main session

- **Found:**
  - On rendered rock/paper/scissors hands, DINOv2-small q8 with kNN needs about 5 to 10 examples per class (2 classes: 84 % / 92 %).
  - k=1 beats k=3 everywhere, and by far with 20-against-3 teaching (60.6 % against 34.5 % for the small class).
  - The raw margin is badly scaled (ECE 0.72), and `0.5 + 0.5*min(1, margin/0.075)` brings that to 0.05 on held-out splits.
  - Never-taught pictures cannot be told apart at a low cost.
- **Fixed:** nothing; no product code was touched.
- **Needs the maintainer:**
  - the S-235 contract choices (fewest examples, k, `.score`, "does not know");
  - pinning a SHA-256 for the DINOv2 q8 file: the earlier spike gave none, and this run found `c179f8f7…7efb`;
  - whether to repeat this on real photos (Imagenette, or webcam pictures).
- **Commits to review:** the plan commit, the scripts commit and the results commit on `cloud/teach-evidence`, all marked [skip ci].

---

# Follow-up: real photographs (Imagenette)

2026-11-05, 07:50 to 07:54 UTC, the same branch. Files are in `imagenette/`: `embed_in.py`, `analyse_in.py` and `results.json`.

- **Data:** Imagenette 160 px from fast.ai (`https://s3.amazonaws.com/fast-ai-imageclas/imagenette2-160.tgz`, 99,003,388 bytes,
  SHA-256 `64d0c4859f35a461889e0147755a999a48b49bf38a7e0f9bd27003f10db02fe5`). From the train split I drew 150 per class across all
  10 classes (seed 0), 1,500 in all. These are real photos of ten very different things: a fish, a dog, a cassette player, a chainsaw,
  a church, a horn, a lorry, a petrol pump, a golf ball and a parachute.
- **Model and set-up:** the same model file and preprocessing as above. The 160 px pictures are scaled up to 256 before the 224 crop.
  Embedding took 84 s on 4 processes at 1 thread each.
- **Run:** `analyse_in.py <prefix> results.json 2000`, seed 235, k=1, 2,000 splits per setting and 40 test pictures per class. Each
  split draws its classes from the 10.

## 1. Accuracy (k=1), against Rock Paper Scissors

| Classes | 3 per class | 5 per class | 10 per class | RPS with 5 per class |
|---|---|---|---|---|
| 2 | 98.7 % | 99.2 % | 99.5 % | 84.4 % |
| 3 | 97.8 % | 98.5 % | 99.1 % | 75.2 % |
| 4 | 97.1 % | 98.1 % | 98.7 % | not measured |
| 5 | 96.4 % | 97.5 % | 98.5 % | not measured |

Intervals and the learner's range for each cell are in `imagenette/results.json`.

- Real photos of **very different things are easy**: 3 examples a class already give 96 to 99 %.
- Rendered hands on plain white are **hard**: they were 15 to 23 points lower with 5 examples a class.
- **The difficulty comes from how alike the classes look, not from whether the pictures are real.** A learner teaching "my cup" against
  "my pen" will probably land between the two datasets. A learner teaching "thumbs up" against "thumbs down" in the same room will
  probably sit near RPS or below it (unverified). So the "at least 5" advice should stand as the safe side; on easy classes 3 is enough.

## 2. The score's floor and scale

On the test splits (the odd-numbered ones; fitted on the even-numbered ones):

| Margin | 0–0.01 | 0.01–0.02 | 0.02–0.05 | 0.05–0.1 | 0.1–0.15 | 0.15–0.2 | 0.2–0.3 | >0.3 |
|---|---|---|---|---|---|---|---|---|
| How often right | 46 % | 55 % | 69 % | 88 % | 96 % | 99 % | 99.8 % | 100 % |

How often a near-tie (margin under 0.01) is right, by the number of classes: **2: 52 %, 3: 49 %, 4: 45 %, 5: 45 %**. With 1/n those
would be 50, 33, 25 and 20 %.

| Floor | Fitted M | ECE, all | ECE with 2 / 3 / 4 / 5 classes | ECE with M fixed at 0.075 |
|---|---|---|---|---|
| fixed 0.5 | 0.1025 | **0.0044** | 0.0031 / 0.0044 / 0.0043 / 0.0054 | 0.0071 |
| 1/n | 0.0725 | 0.0085 | 0.0029 / 0.0063 / 0.0088 / 0.0119 | 0.0085 |

- **The floor should stay at about 0.5, not 1/n.** A margin of 0 does not mean "guessing among all n". It means "a tie between the top
  two", and the true class is nearly always one of those two. So a near-tie is right about half the time, whatever n is. It sinks only
  a little as n grows (45 % at 5 classes). The 1/n floor is worse on held-out splits, and it gets worse as the class count grows.
- If the maintainer wants n in the formula, `max(0.45, 1/n)`-style tuning would be the size of the effect. Data from more than 5
  classes would be needed to justify it (not measured).
- **The scale moves with the data.** The fitted M is 0.075 on RPS and 0.10 on Imagenette. With 0.075 fixed, the ECE on Imagenette is
  still only 0.007.
  - Caveat: the ECE is tiny here mainly because nearly every guess is right, which makes it easy to score well.
  - A single M between 0.075 and 0.1 is defensible for both datasets. I'd suggest **0.1**, the rounder number, which is slightly
    cautious on hard data. On RPS, 0.1 was not tested directly, so this is unverified there.

## 3. `.score` when only one class has been taught (a proposal, not measured)

With one class there is no runner-up, so there is no margin, and every picture is "that class".

- Proposal: `.guess` returns that class and `.score` is **0.5**, with a plain warning: "Teach at least two things so I can compare."
- Why 0.5: it is the same value as a tie, so its meaning matches the rest of the scale ("I cannot tell"). It does not pretend to be
  sure, and it never needs a special case for `None` in learners' `if` statements.
- The rejected alternatives:
  - **Top similarity as the score:** on both datasets, untaught pictures score 0.85 to 0.95 too, so it would look confident about
    anything.
  - **`None`:** it breaks `if guess.score > 0.8:` in learner code.

## For the main session (follow-up)

- **Found:**
  - Real photos of different things are easy (96 to 99 % with 3 examples a class, 2 to 5 classes). Look-alike classes are where
    examples matter.
  - The score's floor should be a fixed 0.5, not 1/n: a near-tie is right 45 to 52 % of the time with 2 to 5 classes, and 1/n does
    worse on held-out splits.
  - The scale M is 0.075 (RPS) to 0.10 (Imagenette); 0.1 is proposed.
  - The one-class case: propose `.score = 0.5` and a warning.
- **Still not measured:** pictures from a learner's own webcam (the maintainer's suggested next test), more than 5 classes, and k=3
  on Imagenette.
- **Commit to review:** the Imagenette scripts and results commits on `cloud/teach-evidence`, both marked [skip ci].

---

# For the main session

Both runs finished; there are no partial numbers and no jobs still running.

- **Found:**
  - On Rock Paper Scissors (rendered hands, 3 classes), k=1 beats k=3 in every clean setting by 5 to 8 points. It is far better
    with uneven teaching (20 against 3: 61 % against 35 % for the small class). With 1 of 5 labels wrong the two are a tie
    (62 % against 61 %).
  - Real photos of different things (Imagenette, 2 to 5 classes) reach 96 to 99 % with 3 examples a class. Look-alike classes are
    where examples matter.
  - The raw margin ranks guesses well but is on the wrong scale. The proposal `0.5 + 0.5 * min(1, margin / M)` with M between 0.075
    and 0.1 calibrates well on held-out splits. The floor should stay 0.5, not 1/n: a near-tie is right 45 to 52 % of the time with
    2 to 5 classes.
  - Untaught pictures score as high as taught ones, so a "does not know" threshold is costly.
- **Fixed:** nothing. Only spike files were added; nothing in `funground/` or `ml/` changed.
- **Needs the maintainer:**
  - the S-235 contract row: k=1 fixed, the `.score` formula and its constant, `.score = 0.5` with a warning when one class is taught,
    and no "does not know" by default;
  - pinning the DINOv2 q8 file (this session's file: SHA-256 `c179f8f7…7efb`, 24,446,700 bytes);
  - a small test with pictures from a real webcam before the row is final.
- **Commits to review** on `cloud/teach-evidence`, all marked [skip ci]: c8ae78a (plan), 6627bcf (scripts), 0c53fbc (RPS results),
  plus the times-correction commit, fb5c231 (Imagenette scripts), ee63f26 (Imagenette results), and this closing commit.
