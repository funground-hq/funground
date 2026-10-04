"""Music: ear training

The sketch plays two notes. The first is your starting note. The second is a mystery, higher
than the first. Say how far up it is. In "swara" mode the starting note is Sa, and you name the
swara you heard (a small letter is komal, flat, and a capital M is tivra, sharp). In "interval"
mode the starting note changes, and you name the gap between the notes, like a minor 3rd.
Answer by clicking a button, by pressing the swara's letter (or the left and right keys, then
Enter), or by singing the second note and holding it steady. The singing is read from the
microphone: each pitch is folded into one octave, and the middle of the last five readings is
used. The ladder shows the right answer with its two notes. With no microphone, clicks and keys
still work. Space plays the notes again, and Enter or N asks the next question.
"""
import math

import funground as f

SA = "D4"
SWARAS = "S r R g G m M P d D n N".split()        # steps 0 to 11 above Sa
INTERVALS = ["minor 2nd", "major 2nd", "minor 3rd", "major 3rd", "4th", "tritone",
             "5th", "minor 6th", "major 6th", "minor 7th", "major 7th", "octave"]    # steps 1 to 12
STARTS = ["C4", "D4", "E4", "F4", "G4"]           # the starting notes in interval mode
HOLD = 20                                         # frames a sung note must stay the same

try:
    mic = f.microphone()
    mic.start()
except RuntimeError:
    mic = None                                    # no microphone: clicks and keys still work

mode = 1                  # 1 swara, 2 interval
question = {}             # start (a note name), start_hz and steps (the right answer)
answered = False
picked = None             # the steps the learner chose
score = 0
asked = 0
streak = 0
best = 0
cursor_at = 0             # which button the arrow keys are on
recent = []               # the last five sung readings, in steps above the start
held = 0                  # how many frames in a row the sung note has been the same
held_note = None
quiet_until = 0           # the microphone waits until the notes have finished playing
playing = None
message = ""
buttons = []              # (x, y, w, h, steps) for each answer button, set while drawing


def steps_of(button):
    """The number of steps above the start that a button stands for."""
    return button if mode == 1 else button + 1


def name_of(steps):
    return SWARAS[steps] if mode == 1 else INTERVALS[steps - 1]


def new_question():
    global question, answered, picked, recent, held, held_note, message
    low = 0 if mode == 1 else 1
    before = question.get("steps")
    steps = f.random_choice([n for n in range(low, low + 12) if n != before])
    start = SA if mode == 1 else f.random_choice(STARTS)
    question = {"start": start, "start_hz": f.note_to_frequency(start), "steps": steps}
    answered, picked, recent, held, held_note = False, None, [], 0, None
    message = "which swara is the second note?" if mode == 1 else "how far up is the second note?"
    play_question()


def play_question():
    """Both notes, in a small room. The microphone then waits for the sound to end."""
    global playing, quiet_until
    steps = question["steps"]
    if mode == 1:
        words = f"S:2 {SWARAS[steps]}:3 -:1"
        sound = f.melody(words, tempo=90, sa=SA, tuning="just").reverb(0.15)
    else:
        second = f.frequency_to_note(question["start_hz"] * 2 ** (steps / 12))
        sound = f.melody(f"{question['start']}:2 {second}:3 -:1", tempo=90).reverb(0.15)
    if playing:
        playing.stop()
    playing = sound
    playing.set_volume(0.8)
    playing.play()
    quiet_until = f.millis() + int(playing.duration() * 1000) + 300


def answer(steps):
    """Check an answer: the score and the streak, then play the notes again."""
    global answered, picked, score, asked, streak, best, message
    if answered:
        return
    answered, picked = True, steps
    asked += 1
    if steps == question["steps"]:
        score += 1
        streak += 1
        best = max(best, streak)
        message = "right! it was " + name_of(steps)
    else:
        streak = 0
        message = "not quite. it was " + name_of(question["steps"])
    play_question()


def sung_steps():
    """The note being sung, in steps above the start and in one octave (-0.5 to 11.5), or None."""
    if mic is None or answered or f.millis() < quiet_until:
        return None
    hz = mic.pitch()
    if hz is None:
        return None
    steps = 12 * math.log2(hz / question["start_hz"])
    return (steps + 0.5) % 12 - 0.5               # a note in another octave lands on the same rung


def listen():
    """A sung note held steady (the middle of the last five readings) for a moment is an answer."""
    global held, held_note
    here = sung_steps()
    if here is None:
        held, held_note = 0, None
        del recent[:]
        return
    recent.append(here)
    del recent[:-5]
    note = round(sorted(recent)[len(recent) // 2]) % 12
    if mode == 2 and note == 0:
        note = 12                                 # singing the start note again is the octave
    if note == held_note:
        held += 1
    else:
        held_note, held = note, 1
    if held >= HOLD:
        answer(note)


def mouse_pressed():
    for x, y, w, h, steps in buttons:
        if x <= f.mouse_x <= x + w and y <= f.mouse_y <= y + h:
            answer(steps)
            return


def key_pressed():
    global cursor_at
    key = f.key
    if key == " ":
        play_question()
    elif key in ("n", "N") or (key == "enter" and answered):
        new_question()
    elif key == "left":
        cursor_at = (cursor_at - 1) % 12
    elif key == "right":
        cursor_at = (cursor_at + 1) % 12
    elif key == "enter":
        answer(steps_of(cursor_at))
    elif mode == 1 and key in SWARAS:
        answer(SWARAS.index(key))


def setup():
    global mode_slider, again_button, next_button
    f.size(640, 420)
    mode_slider = f.create_slider(1, 2, 1, step=1, label="mode: 1 swara, 2 interval")
    again_button = f.create_button("hear it again")
    next_button = f.create_button("next question")
    new_question()


def draw():
    global mode, score, asked, streak
    if mode_slider.value() != mode:
        mode = mode_slider.value()
        score = asked = streak = 0
        new_question()
    if again_button.clicked():
        play_question()
    if next_button.clicked():
        new_question()
    listen()

    f.background("#14192b")
    f.no_stroke()
    f.text_align("left", "top")
    f.fill("white")
    f.text_size(22)
    f.text("Ear training: " + ("swaras above Sa" if mode == 1 else "intervals"), 20, 14)
    f.text_size(15)
    f.fill(("#58d68d" if picked == question["steps"] else "#ff7b72") if answered else "gold")
    f.text(message, 20, 46)
    f.fill("#9fb4d8")
    f.text_size(14)
    f.text(f"score {score} of {asked}     streak {streak}     best {best}", 20, 72)
    if mode == 1:
        f.text(f"Sa is {SA}.  A small letter is flat; M is sharp.", 20, 96)
    else:
        f.text(f"the starting note is {question['start']}", 20, 96)

    # the answer buttons, 4 across
    del buttons[:]
    f.text_align("center", "center")
    for i in range(12):
        x, y = 20 + (i % 4) * 100, 128 + (i // 4) * 52
        steps = steps_of(i)
        buttons.append((x, y, 92, 44, steps))
        if answered and steps == question["steps"]:
            f.fill("#2f9e6a")
        elif answered and steps == picked:
            f.fill("#b84a4a")
        else:
            f.fill("#46558a" if i == cursor_at else "#27304d")
        f.rect(x, y, 92, 44, 8)
        f.fill("white")
        f.text(name_of(steps), x + 46, y + 22)

    # what the microphone hears
    f.text_align("left", "top")
    f.text_size(13)
    f.fill("#9fb4d8")
    if mic is None:
        f.text("no microphone found: click or press keys to answer", 20, 300)
    else:
        hearing = f"   (hearing {name_of(held_note)})" if held_note is not None and not answered else ""
        f.text("or sing the second note and hold it" + hearing, 20, 300)
    f.text("space: hear again     enter or n: next question", 20, 322)
    f.text("arrow keys and enter: answer", 20, 342)

    # the ladder: one rung for each step above the start
    f.text_align("left", "center")
    for step in range(13):
        y = 380 - step * 25
        shown = answered and step in (0, question["steps"])
        if shown:
            f.fill("deepskyblue" if step == 0 else "gold")
        else:
            f.fill("#27304d")
        f.rect(450, y - 11, 170, 22, 5)
        f.fill("black" if shown else "#6f7fa8")
        if shown:
            note = f.frequency_to_note(question["start_hz"] * 2 ** (step / 12))
            f.text(f"{'start' if step == 0 else 'answer'}: {note}", 458, y)
        else:
            f.text(str(step), 458, y)
    f.fill("#9fb4d8")
    f.text_align("left", "bottom")
    f.text_size(12)
    f.text("steps above the start", 450, 410)


f.run()
