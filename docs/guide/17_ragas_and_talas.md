# 17. Ragas and talas

This chapter is for anyone learning Hindustani (North Indian) classical music, or curious about it.
funground can play a drone to sing with, play a raga's notes and a tala's drum pattern, and listen
to a recording to say which notes were sung. It builds on [Sargam](16_sound.md#sargam) in chapter 16:
`f.melody(text, sa="D4")` reads the swaras `S r R g G m M P d D n N`.

A word of warning first. A raga is much more than its notes. It has its own way of moving between
them, its ornaments, its resting notes and its mood, and these are learnt from a teacher by
listening. funground knows a raga's notes and a few facts about it. That is a start, not the raga.

## The raga table

funground has a small table of well-known ragas, the kind a learner meets early. `f.ragas()` lists
their names. `f.raga(name)` gives one of them. Capitals do not matter, so `f.raga("yaman")` works,
and a name that is not in the table gives a `ValueError` that lists the ones that are.

```py
yaman = f.raga("Yaman")
yaman.thaat         # 'Kalyan'
yaman.swaras        # ('S', 'R', 'G', 'M', 'P', 'D', 'N')
yaman.aroha         # "N, R G M P D N S'"   the way up
yaman.avaroha       # "S' N D P M G R S"     the way down
yaman.pakad         # 'N, R G R S P M G R S' a phrase that marks the raga
yaman.vadi, yaman.samvadi   # ('G', 'N') the two most important swaras
yaman.time          # the traditional time of day to perform it
yaman.notes         # where the sources differ, and other things to know
yaman.sources       # where each fact was checked
```

- The **thaat** is the parent scale it belongs to, in Bhatkhande's system of ten.
- The **swaras** are the notes it uses. Small `r g d n` are komal (flat). `M` is tivra (sharp) Ma.
- The **aroha**, **avaroha** and **pakad** are sargam strings you can give straight to
  `f.melody(..., sa=...)`.
- The **vadi** is the most important note and the **samvadi** the second.
- The **time** is the prahar, the three-hour part of the day or night, that the raga belongs to.

| Raga | Thaat | Swaras | Vadi, samvadi | Time |
|---|---|---|---|---|
| Yaman | Kalyan | `S R G M P D N` | G, N | evening: the first prahar of the night, about 6 to 9 pm |
| Bhupali | Kalyan | `S R G P D` | G, D | evening: the first prahar of the night, about 6 to 9 pm |
| Bilawal | Bilawal | `S R G m P D n N` | D, G | morning: the first prahar of the day, about 6 to 9 am |
| Khamaj | Khamaj | `S R G m P D n N` | G, N | night: the second prahar, about 9 pm to midnight |
| Kafi | Kafi | `S R g m P D n` | P, S | night: the second prahar, about 9 pm to midnight |
| Bhairav | Bhairav | `S r G m P d N` | d, r | dawn: the first prahar of the day, about 6 to 9 am |
| Asavari | Asavari | `S R g m P d n` | d, g | late morning: the second prahar of the day, about 9 am to noon |
| Bhairavi | Bhairavi | `S r g m P d n` | m, S | morning: the first prahar of the day; by custom it ends a concert, at any hour |
| Todi | Todi | `S r g M P d N` | d, g | late morning: the second prahar of the day, about 9 am to noon |
| Marwa | Marwa | `S r G M D N` | r, D | sunset: the end of the fourth prahar of the day, about 4 to 7 pm |
| Durga | Bilawal | `S R m P D` | m, S | night: the second prahar, about 9 pm to midnight |
| Desh | Khamaj | `S R G m P D n N` | R, P | night: the second prahar, about 9 pm to midnight |
| Deshkar | Bilawal | `S R G P D` | D, G | morning: the first prahar of the day, about 6 to 9 am |

**Where these facts come from.** Every raga and tala was checked against at least two published
sources, such as Tanarang, SwarGanga, Rajan Parrikar's essays, NCERT and NIOS textbooks, and
Wikipedia articles that cite *The Raga Guide* (Bor and others) and Kaufmann. The sources are listed
with each raga in `sources`. Teachers and gharanas do not always agree. Kafi's samvadi is Sa in some
books and Re in others; Bhairavi's vadi is debated; every raga's pakad is written a little
differently by different teachers. Where that happens, the table gives the most common form and
`notes` says what else you may be taught. If your teacher says otherwise, follow your teacher.

## The drone

A tanpura plays Sa and Pa over and over, so a singer always has Sa to hold on to. `f.drone(sa,
seconds)` makes a sound like one: plucked strings that ring on, one after another. Give it Sa as a
note name such as `"D3"`. It loops smoothly, with no gap, when you call `loop()`.

The strings are given by `pattern`, which is `"P S' S' S"` unless you say otherwise: Pa, then
upper Sa twice, then Sa. For a raga without Pa, a tanpura's first string is tuned to another note,
often Ma or Ni, and you can do the same: `f.drone("D3", 8, pattern="m S' S' S")` or
`pattern="N S' S' S"`. Ask your teacher which suits the raga. The strings are tuned in just
intonation, so Pa is exactly 3/2 of Sa, as a tanpura is tuned by ear.

Here is Yaman's aroha and avaroha over a drone, with each swara lit as it plays.

```python
import funground as f

SA = "D4"
tokens = (f.raga("Yaman").aroha + " - " + f.raga("Yaman").avaroha + " -").split()
tune = f.melody(" ".join(tokens), tempo=90, wave="triangle", sa=SA, tuning="just")
drone = f.drone("D3", tune.duration())


def setup():
    f.size(560, 160)
    tune.loop()
    drone.loop()


def draw():
    f.background("#201830")
    now = int(tune.current_time() / (60 / 90))
    f.text_size(20)
    for i, token in enumerate(tokens):
        f.fill("gold" if i == now else "#a090c0")
        f.text(token, 20 + i * 30, 70)


f.run()
```

It is an approximation. A real tanpura's buzzing richness comes from its curved bridge (jawari), and
that is very hard to copy.

## Meend and kan

Indian music moves between notes as much as it lands on them. `f.melody` has two ornaments for this.

- **Meend** is a glide. `S~G` slides smoothly from S to G over the token's beats. `G~R:2` slides
  down over two beats.
- **Kan** is a grace note: a quick touch of one note before another. `(R)G` touches R for about
  60 thousandths of a second, then plays G.

```py
f.melody("S R (R)G:2 G~R:2 S", sa="D4")       # a kan on Ga, then a meend down to Re
f.melody("C4~E4:2 (D4)E4", tempo=80)           # they work with note names too
```

Both keep the wave unbroken as the pitch changes, so there is no click. A gamaka, a shake around a
note, is not built in yet.

## Talas

A tala is a cycle of beats (matras) that comes round again and again. The beats fall in groups, the
vibhags. You clap at the start of some groups (tali) and wave at the start of others (khali). Beat 1
is the sam, where the cycle begins and lands; it is marked X. A wave is marked 0. The theka is the
pattern of bols, the syllables that name the tabla strokes, one bol a beat.

`f.talas()` lists the six in the table. `f.tala_info(name)` gives one of them: `beats`, `vibhag` (the
group sizes), `tali` and `khali` (beat numbers, counted from 1), `sam` and `bols`.

| Tala | Beats | Vibhag | Tali (claps) | Khali (waves) | Theka |
|---|---|---|---|---|---|
| Teentaal | 16 | 4+4+4+4 | 1, 5, 13 | 9 | Dha Dhin Dhin Dha \| Dha Dhin Dhin Dha \| Dha Tin Tin Ta \| Ta Dhin Dhin Dha |
| Ektaal | 12 | 2+2+2+2+2+2 | 1, 5, 9, 11 | 3, 7 | Dhin Dhin \| DhaGe TiRaKiTa \| Tu Na \| Kat Ta \| DhaGe TiRaKiTa \| Dhin Na |
| Jhaptaal | 10 | 2+3+2+3 | 1, 3, 8 | 6 | Dhi Na \| Dhi Dhi Na \| Ti Na \| Dhi Dhi Na |
| Rupak | 7 | 3+2+2 | 4, 6 | 1 | Tin Tin Na \| Dhin Na \| Dhin Na |
| Dadra | 6 | 3+3 | 1 | 4 | Dha Dhin Na \| Dha Tin Na |
| Keherwa | 8 | 4+4 | 1 | 5 | Dha Ge Na Ti \| Na Ka Dhi Na |

Rupak is the odd one out: its sam is a wave, not a clap. Spellings of the bols differ between books
(Dhi or Dhin, Tu or Tun), and so do a few bols, which `notes` points out.

`f.tala(name, tempo=80, cycles=1)` plays the theka with simple drum sounds. Dha is a low drum and a
high ring together; Na and Ta ring high; Ge is low; Ka and Ke are short dry slaps; Tin and Tun ring
longer. A bol written as one word, like DhaGe or TiRaKiTa, shares its beat between its strokes. The
sam is played louder and the khali vibhag more softly. The sound lasts exactly `beats * 60 / tempo *
cycles` seconds, so it loops in time.

```python
import funground as f

info = f.tala_info("Jhaptaal")
cycle = f.tala("Jhaptaal", tempo=100)


def setup():
    f.size(520, 120)
    cycle.loop()


def draw():
    f.background("#10202a")
    beat = int(cycle.current_time() / (60 / 100))
    for i, bol in enumerate(info.bols):
        f.fill("gold" if i == beat else "white")
        f.text(bol, 20 + i * 50, 60)
        if i + 1 in info.tali:
            f.text("X" if i + 1 == info.sam else "clap", 20 + i * 50, 30)
        if i + 1 in info.khali:
            f.text("0", 20 + i * 50, 30)


f.run()
```

The drums are synthesised, so they sound like a sketch of a tabla, not a real one. A real tabla's
sound needs recordings.

## Listening: Sa, swaras and ragas

These work on any sound, and on a microphone too (what it heard in the last 10 seconds).

- **`x.tonic()`** guesses Sa, in hertz, or gives `None` if too little had a clear pitch. It follows
  the pitch through the sound, counts how long each pitch was heard (folded into one octave), and
  picks the pitch that best explains a strong Sa and Pa: Sa and Pa are what a drone plays and where
  a melody rests most. It is a guess. It goes wrong when the music has no Pa, when the drone is tuned
  to Ma, or when the melody sits on another note far more than on Sa. If you know your Sa, use it.
- **`x.swara_histogram(sa)`** gives 12 numbers, one for each swara `S r R g G m M P d D n N` above
  `sa` (a note name, or the hertz from `tonic()`): the share of the time each one sounded, in any
  octave, within half a semitone of it. They add up to 1.
- **`f.match_ragas(histogram)`** compares those 12 numbers with every raga in the table and gives
  `(name, score)` pairs, best first, with scores from 0 to 1. A raga scores well when the music stays
  on its swaras, uses all of them, and stresses its vadi and samvadi.

```py
recording = f.load_sound("my_singing.wav")
sa = recording.tonic()                    # or the Sa you know, like "C#4"
shares = recording.swara_histogram(sa)
print(f.match_ragas(shares)[:3])          # for example [('Yaman', 0.85), ('Desh', 0.56), ...]
```

**What it cannot tell apart.** `match_ragas` compares sets of notes. It is a learning aid, not a
raga recogniser. Two ragas that use the same swaras get almost the same score:

- Bhupali and Deshkar both use `S R G P D`. Bhupali dwells on Ga and the lower notes, Deshkar on Dha
  and the upper ones. Only the vadi and samvadi move the scores, a little.
- Bilawal, Khamaj and Desh all use `S R G m P D n N` in this table. A Khamaj phrase can come out
  with Bilawal first.

What really tells such ragas apart is how they move: the order of notes, the phrases, where they rest,
how the notes are approached. A swara histogram throws all of that away. Use it to see which notes you
sang, and listen for the rest.

## Good to know

- **Speed.** Listening follows the pitch about 50 times a second for a short sound and measures at
  most 300 times for a long one, which takes a second or two. Call `tonic()` and `swara_histogram()`
  once, not every frame. A sound remembers its pitch line, so asking twice costs nothing.
- **Tuning.** `swara_histogram` gives each swara the pitches within 50 cents of its equal-tempered
  place. Just-tuned notes are within about 18 cents of those, so they count where you expect.
- **Mistakes.** A raga or tala that is not in the table, a pattern that is not swaras, a tempo of 0 or
  a histogram that is not 12 numbers of 0 or more give a `ValueError` that says what was wrong.

**Previous:** [16. Sound](16_sound.md) · **Next:** [18. Projects](18_projects.md)
