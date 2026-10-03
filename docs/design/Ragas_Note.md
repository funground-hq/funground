# Ragas for learners: sources, methods and limits (S-115)

Status: built in Sprint 14 against contract row A8 (D-057, D-062). This note says where the raga and
tala facts come from, how each feature works, and what it cannot do. The code is
`funground/hindustani.py`, the data `funground/data/ragas.json`, the tests `tests/test_ragas.py`,
and the learner's guide chapter 17.

## 1. The table and its sources

**Contents.** 13 ragas: Yaman, Bhupali, Bilawal (Alhaiya), Khamaj, Kafi, Bhairav, Asavari (shuddha
Re), Bhairavi, Todi (Miyan ki Todi), Marwa, Durga (Bilawal thaat), Desh and Deshkar. Deshkar was
added to the suggested twelve because A8 names the Bhupali and Deshkar pair as the limit the guide
must explain. 6 talas: Teentaal, Ektaal, Jhaptaal, Rupak, Dadra, Keherwa.

**How it was checked (3 October 2026).** Every page below was fetched and read during the build;
the facts were not written from memory. Each raga and tala cites at least two sources, and the
`supports` field of each citation says which facts that source backs. The books most often cited
(Bhatkhande's *Kramik Pustak Malika* and *Hindustani Sangeet Paddhati*, Kaufmann's *The Ragas of
North India* (1968), Bor and others' *The Raga Guide* (1999)) are not freely online; they are cited
only second-hand, through Wikipedia's footnotes and Parrikar's essays. A reviewer with these books
should spot-check the pakads first.

| Source | Used for |
|---|---|
| Tanarang (Acharya V. R. Ringe), tanarang.com raga pages | thaat, swaras, aroha, avaroha, main phrases, vadi, samvadi, time |
| SwarGanga, swarganga.org raag and taal pages | the same for ragas; beats, divisions, tali, khali and theka for talas |
| Rajan Parrikar, parrikar.org essays | phrases, history and disputes (Asavari's Re, Bhairavi's vadi, Pa in Todi, Bhupali and Deshkar) |
| Wikipedia raga and tala articles | a third check; they cite Bor, Kaufmann and Bhatkhande |
| NCERT *Kriti* (class 8) ch. 7; NIOS *Hindustani Music (242)* Practical Book 2 ch. 4 | Asavari; the theka and structure of five talas (NIOS has no rupak) |
| Darbar, darbar.org raga pages | vadi, samvadi, aroha, avaroha and time for Bhairavi, Todi, Durga, Desh |
| David Courtney, chandrakantha.com | tala structure (its thekas are images and were not read) |
| University of Washington, Music 428 thekas page | thekas for all six talas |
| ITC SRA Samay Raga page; raag-hindustani.com; ragajunglism.org; indianclassicalmusic.com | weaker support for single facts (time, vadi) |

**Where sources disagree** (the table gives the most common form; each entry's `notes` says so):

- **Kafi** samvadi: Sa (Tanarang) or Re (SwarGanga, Wikipedia). Pa and Sa chosen. Kafi and Khamaj
  time: 9 pm to midnight (Tanarang, Bor via Wikipedia) or 6 to 9 pm (SwarGanga).
- **Bhairavi** vadi: Ma (Tanarang, Darbar, Parrikar), Ma or Pa (Wikipedia), komal Dha (R. Jha,
  quoted by Parrikar). Ma and Sa chosen.
- **Durga** vadi: Ma in five sources, Pa in Darbar alone. Ma and Sa chosen.
- **Marwa** vadi: Re and Dha is standard; Patwardhan argued for Dha and Ga. Time 3 to 6 pm
  (Tanarang) or 4 to 7 pm (ITC SRA); all say sunset.
- **Todi**: Pa left out going up (Bor, ITC SRA) or printed but "generally skipped" (Tanarang,
  Darbar). The table leaves it out of the aroha.
- **Asavari**: shuddha Re (Bhatkhande, Gwalior) or komal Re (the older dhrupad form); the table has
  shuddha Re. NCERT's summary table names the Bhairavi thaat, against its own text; not followed.
- **Bilawal**: Alhaiya Bilawal (komal Ni in descent) is given, as Parrikar treats the names as one
  raga; Shuddha Bilawal is a separate raga.
- **Yaman**: Wikipedia's text says 9 pm to midnight, against "first prahar of the night" in Tanarang
  and SwarGanga; the latter chosen.
- **Desh** time: Wikipedia's infobox says late night; its text and two other sources say 9 pm to
  midnight.
- **Pakad**: every raga's is written differently by different teachers. Each entry says whose it is.
- **Talas**: teentaal beat 13 is Ta (SwarGanga, NIOS) or Na (UW); ektaal's beats 5 and 8 are Tu or
  Tun and Ta or Tin; jhaptaal is spelt Dhi/Ti (NIOS) or Dhin/Tin; rupak's claps are numbered 2 and 3
  or 1 and 2. Wikipedia's Dadra theka (one weak citation) contradicts every other source and was not
  used.

## 2. Methods

**Meend and kan** (`synth.ornament_samples`). One note whose frequency changes sample by sample, with
the wave's phase carried along, so there is no click. A meend moves from the first pitch to the
second on a smoothstep curve in log-frequency over the whole token. A kan holds the grace pitch for
60 ms (at most half the token), then the main note. The token's usual 10 ms attack and 50 ms release
apply once, to the whole token.

**Drone** (`hindustani.drone`). Karplus-Strong strings, like `synth.pluck`, with a softer pluck (the
noise burst is smoothed 32 times) and a loop loss set for a 6-second fall of 60 dB. Strings are tuned
in just intonation from Sa. They are plucked 0.7 s apart, with one extra gap after the last; each
rings for 5 s. Tails that run past the end are added back at the start, so `loop()` has no gap.
Largest sample-to-sample step about 0.2 at a 0.8 peak.

**Tala** (`hindustani.tala`). Each bol is split at its capital letters into strokes (DhaGe is Dha and
Ge), which share the beat. Strokes are synthesised: a bass thud falling from 120 to 75 Hz (Ge); a
dayan ring at 280 Hz with decaying partials, short and bright (Na, Ta), long and pure (Tin, Tun), or
soft and short (Ti, Ra); a damped noise slap (Ka, Ke, Kat). Dha and Dhin are bass plus ring. The sam
is played at full strength, other beats at 0.7, and the beats of a khali vibhag at 0.6 of that. The
sound is cut at exactly beats × 60 / tempo × cycles seconds, with a 5 ms fade.

**Pitch track** (`hindustani.pitch_track`). The samples are averaged in blocks of four (to about
11 025 a second), then `synth.find_pitch` (the autocorrelation of `sound.pitch()`) is run on
1 024-sample windows every 20 ms, at most 300 times over the sound. A sound keeps its track; a
microphone's last 10 seconds are tracked afresh on each call.

**Tonic.** Pitches are folded to one octave in cents, counted into 120 bins of 10 cents (each pitch
split between its two nearest bins) and smoothed over ±20 cents. Sa is the bin with the largest count
plus the count 702 cents above it (a strong Sa–Pa pair). The exact pitch is the mean of the pitches
within 30 cents of that bin; the octave is the one in which that pitch class was heard most. `None`
below 10 pitched measurements.

**Swara histogram.** Each pitched measurement goes to the nearest equal-tempered swara above Sa (±50
cents), any octave; the counts are divided by their total.

**Match.** For a raga with k swaras: fit = the share of the histogram on its swaras; coverage = the
mean over its swaras of min(1, 4k × share), so a swara counts once it has a quarter of an even share;
stress x = (2 × vadi share + samvadi share) × k / 3, mapped to x / (1 + x). Score = fit² × coverage ×
(0.85 + 0.15 × stress), rounded to 4 places, from 0 to 1.

## 3. Measured results

- **Tonic**: a sargam phrase in just tuning, alone and mixed with a drone an octave below, for Sa =
  D4, C#4, A3 and G4: every estimate within 6 cents of the true Sa, in the right octave.
- **Match**, on each raga's own aroha, avaroha and pakad (Sa = D4, equal tuning): the raga itself
  comes first for 12 of the 13. Bhupali and Deshkar come out level to two places on each other's
  phrases (0.81 and 0.81 on Bhupali's, 0.85 and 0.85 on Deshkar's); the vadi puts the right one first. Khamaj's phrases rank Bilawal first (0.88 against 0.86), because
  Bilawal, Khamaj and Desh have the same swara set in this table. The nearest other raga is usually
  far behind (Yaman 0.85, then Desh 0.56; Bhairav 0.90, then Bhairavi 0.40).

## 4. Limits

- **Notes, not ragas.** Matching compares note sets. Ragas with the same swaras (Bhupali and Deshkar;
  Bilawal, Khamaj and Desh) cannot be told apart except a little by vadi and samvadi. Movement,
  phrases, resting notes, ornaments and time are all lost in a histogram.
- **Tonic** fails without a strong Pa (Marwa; a drone tuned to Ma) and when a melody dwells on another
  note far more than on Sa. Published methods (Gulati and others, 2014, Music_Research_Note §6.3) reach
  about 90% with multipitch analysis and machine learning; this is a simple heuristic.
- **Pitch tracking** follows one voice. With a loud drone under a quiet voice it may follow the drone.
  Above about 1 kHz its resolution falls (the copy is at 11 025 samples a second).
- **Tuning.** Swaras are binned around equal-tempered places; shrutis and the fine intonation of
  particular ragas (such as the slow oscillation, andolan, of Bhairav's komal Re and Dha) are not modelled.
- **Sounds.** The drone has no jawari buzz and the drums are a sketch of a tabla.
- **Data.** The table is small and Hindustani only; Carnatic melakartas are later (D-062).

## 5. Deviations from the brief

- The brief suggested `funground/ragas.py`. A submodule named `ragas` would replace the public
  function `f.ragas` on the package as soon as it is imported (Python sets the attribute), so the
  module is `funground/hindustani.py`.
- "Play the khali vibhag lower" was read as *softer* (0.6 of the strength), not lower in pitch; the
  theka itself already drops the bass strokes there (Dha becomes Ta, Dhin becomes Tin).
- The drone's click bound in the tests is a step of 0.25 per sample, not a smaller number: the soft
  pluck's own brightest part moves by about 0.2.
