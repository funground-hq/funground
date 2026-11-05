# S-235 evidence: teach and guess from a few camera pictures

Started 2026-11-05 07:42 UTC. Branch: cloud/teach-evidence.

## Plan
1. Embed up to 1,500 Rock Paper Scissors pictures with DINOv2-small q8 (pinned file), 4 processes x 1 thread; save .npy outside git.
2. kNN (k = 1, 3) over 2,000+ seeded splits: 1/2/3/5/10/20 per class, 2/3 classes; accuracy with 95% intervals.
3. Calibration of top-minus-runner-up score: bins, a 0-1 mapping fitted on one set of splits and tested on others.
4. Left-out class: how high it scores; a does-not-know threshold and its cost. 5. Bad teaching: 1-in-5 wrong labels; 20 against 3.
