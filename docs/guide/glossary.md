# Glossary

Short meanings for the words this guide uses. Each one links to the chapter that teaches it.
Stuck on an error message instead? See [When something goes wrong](errors.md).

## A

- **alpha**. How solid a colour is. 0 is invisible and 255 is solid. [Chapter 4](04_colour.md)
- **aroha**. The way a raga goes up, from Sa to the Sa above. See also *avaroha*. [Chapter 17](17_ragas_and_talas.md#the-raga-table)
- **avaroha**. The way a raga comes down. [Chapter 17](17_ragas_and_talas.md#the-raga-table)

## B

- **beat**. One step of the pulse of a tune. `tempo` says how many beats come each minute. [Chapter 16](16_sound.md#beats-and-tempo)
- **blend mode**. The rule for how new drawing mixes with what is already there, such as `"multiply"`. [Chapter 5](05_fill_stroke_lines.md#mixing-see-through-and-shadows)
- **bol**. The name of a tabla stroke, said as a syllable: Dha, Dhin, Na, Tin. A theka is a line of bols. [Chapter 17](17_ragas_and_talas.md#talas)
- **boolean (shapes)**. Joining or cutting two paths to make a new one: union (`|`), intersection (`&`), difference (`-`) and xor (`^`). [Chapter 9](09_paths_and_clipping.md#combining-shapes)

## C

- **canvas**. The drawing area. Its size is set with `f.size()`. [Chapter 2](02_the_sketch.md)
- **chord**. Two or more notes played together. `f.melody()` writes one as `[C4 E4 G4]`, and `sound.chord()` names the one it hears. [Chapter 16](16_sound.md#chords-and-keys)
- **clip**. To keep drawing inside a path. Anything outside the path is not painted. [Chapter 9](09_paths_and_clipping.md#clipping)
- **colour mode**. How numbers are read as a colour: `"rgb"`, `"hsb"` or `"hsl"`, and the largest value of each part. Set with `f.color_mode()`. [Chapter 4](04_colour.md#colour-mode)
- **coordinates**. A place on the canvas as a pair of numbers, `x` across and `y` down, from the top-left corner. [Chapter 1](01_getting_started.md#where-things-are)

## D

- **decibel (dB)**. A way to measure loudness on a scale where each step of 20 is ten times the sound level. A quiet room is about -65 dB in funground's microphone examples. [Chapter 16](16_sound.md#listening-with-the-microphone)
- **draw**. The function `draw()` that funground calls once for every frame. [Chapter 2](02_the_sketch.md)
- **drone / tanpura**. A steady background note, or the instrument that plays it. A tanpura sounds Sa and Pa over and over, so a singer always has Sa to hold on to. `f.drone()` makes one. [Chapter 17](17_ragas_and_talas.md#the-drone)

## E

- **envelope**. The shape of a note over time: how it rises (attack), settles (decay), holds (sustain) and fades (release). [Chapter 16](16_sound.md#the-shape-of-a-note)

## F

- **fill**. The colour inside a shape. Set with `f.fill()`. [Chapter 5](05_fill_stroke_lines.md)
- **font fallback**. Drawing a letter from another font when the one you chose does not have it, so you see the letter, not an empty box. [Chapter 6](06_text.md#letters-your-font-does-not-have)
- **frame**. One run of `draw()`: one picture in the animation. About 60 happen each second. [Chapter 2](02_the_sketch.md)
- **frequency**. How many times a sound wave goes up and down each second, in hertz (Hz). 440 Hz is the note A above middle C. [Chapter 16](16_sound.md#making-sound)

## G

- **gradient**. A colour that changes smoothly from one place to another. It can be used wherever a colour can. [Chapter 4](04_colour.md#gradients)

## H

- **hex colour**. A colour written like a web page does, such as `"#FF6347"`. [Chapter 4](04_colour.md)
- **hue**. The "kind" of colour, as a position on the colour wheel: 0 is red, 120 is green and 240 is blue. [Chapter 4](04_colour.md#colour-by-hue)

## K

- **kan**. A quick grace note touched just before another note, written `(R)G`. [Chapter 17](17_ragas_and_talas.md#meend-and-kan)
- **khali**. The "empty" part of a tala, marked by a wave of the hand instead of a clap and written 0. [Chapter 17](17_ragas_and_talas.md#talas)

## L

- **layer**. A see-through picture over the canvas that keeps its drawing. Made with `with f.layer("name"):`. Layers are real layers in a PDF or SVG. [Chapter 9](09_paths_and_clipping.md#layers)
- **live text**. Text in a PDF or SVG file that is still text, so you can select, search and edit it. The other choice is *shapes* (see below). [Chapter 13](13_saving_your_work.md#text-in-an-svg-file)

## M

- **meend**. A smooth glide from one note to another, written `S~G`. [Chapter 17](17_ragas_and_talas.md#meend-and-kan)
- **microphone**. Your computer's sound input. `f.microphone()` listens to it and tells you its level, spectrum and pitch. [Chapter 16](16_sound.md#listening-with-the-microphone)

## N

- **noise**. A smooth kind of randomness. `f.noise()` changes gently as you move along it, like hills, not like static. [Chapter 11](11_randomness_and_noise.md#noise-smooth-randomness)

## O

- **onset**. The moment a new note or hit begins in a sound. [Chapter 16](16_sound.md#beats-and-tempo)
- **opacity**. How see-through everything you draw is. `f.opacity()` goes from 0 (invisible) to 255 (solid). [Chapter 5](05_fill_stroke_lines.md#mixing-see-through-and-shadows)

## P

- **pakad**. A short phrase that marks a raga, the one that tells a listener which raga it is. [Chapter 17](17_ragas_and_talas.md#the-raga-table)
- **path**. A shape built from lines and curves, made with `f.path()`. You can draw it, clip with it, and join or cut paths. [Chapter 9](09_paths_and_clipping.md#reusable-paths)
- **PDF**. A file for documents and print. funground saves the shapes and text, so it stays sharp at any size. [Chapter 13](13_saving_your_work.md)
- **picture**. A canvas of its own that you can draw on and then place with `f.image()`. Made with `f.create_graphics()`, `f.load_image()` or `f.load_svg()`. [Chapter 9](09_paths_and_clipping.md#drawing-off-screen)
- **pitch**. How high or low a note sounds. `sound.pitch()` gives the frequency of the note it hears. [Chapter 16](16_sound.md#which-note-is-it)
- **pixel**. One tiny dot of the canvas. The canvas is a grid of them. [Chapter 9](09_paths_and_clipping.md#pixels)
- **push and pop**. `f.push()` saves the transform and style, and `f.pop()` brings them back. `with f.saved_state():` does both for you. [Chapter 8](08_transforms.md)

## R

- **raga**. A set of notes with its own rules and mood, used to make Hindustani music. funground knows a raga's notes and a few facts, not the raga itself. [Chapter 17](17_ragas_and_talas.md)
- **reverb**. The ringing of a room after a sound ends. `sound.reverb()` adds it. [Chapter 16](16_sound.md#a-room-for-the-sound)

## S

- **Sa**. The first and home note of Indian music. Every other swara is measured from it, and it can be any pitch you like. [Chapter 17](17_ragas_and_talas.md)
- **sam**. The first beat of a tala, where the cycle begins and lands. Marked X. [Chapter 17](17_ragas_and_talas.md#talas)
- **sample**. One number in a sound. A sound is a long list of samples from -1 to 1, 44 100 of them for each second. [Chapter 16](16_sound.md#the-numbers-inside-a-sound)
- **samvadi**. The second most important swara of a raga. See also *vadi*. [Chapter 17](17_ragas_and_talas.md#the-raga-table)
- **script**. A file with no `setup()`, `draw()` or `f.run()`. It draws from top to bottom, and ends with `f.show()` or `f.save()`. [Chapter 2](02_the_sketch.md#scripts-drawing-without-draw)
- **setup**. The function `setup()` that funground calls once, before the first frame. Usually it calls `f.size()`. [Chapter 2](02_the_sketch.md)
- **shapes (text as)**. Saving every letter as a drawing of its outline, so it looks the same on every computer but cannot be edited. Written `text="shapes"`. [Chapter 13](13_saving_your_work.md#the-golden-rule-of-svg-handoffs)
- **sketch**. A funground program with `setup()` and `draw()` that ends with `f.run()`. [Chapter 1](01_getting_started.md)
- **sound**. A made or loaded noise you can play, watch and change. In funground it is an object with `play()`, `level()`, `spectrum()` and more. [Chapter 16](16_sound.md)
- **spectrum**. The strength of each range of pitch in a sound at this moment, from low notes to high ones. Often drawn as bars. [Chapter 16](16_sound.md#watching-the-sound)
- **stroke**. The outline of a shape, or a line. Set with `f.stroke()` and `f.stroke_width()`. [Chapter 5](05_fill_stroke_lines.md)
- **SVG**. A file of shapes and text for the web and for drawing programs. [Chapter 13](13_saving_your_work.md)
- **swara**. A note of Indian music, named from Sa: `S r R g G m M P d D n N`. Small letters are flat (komal) and `M` is sharp (tivra). [Chapter 17](17_ragas_and_talas.md)

## T

- **tala**. A cycle of beats that comes round again and again, such as Teentaal with 16 beats. [Chapter 17](17_ragas_and_talas.md#talas)
- **tali**. The beats of a tala where you clap. [Chapter 17](17_ragas_and_talas.md#talas)
- **tanpura**. See *drone*.
- **tempo**. The speed of the beat, in beats a minute. [Chapter 16](16_sound.md#beats-and-tempo)
- **thaat**. The parent scale a raga belongs to, in Bhatkhande's system of ten. [Chapter 17](17_ragas_and_talas.md#the-raga-table)
- **theka**. The pattern of bols that sets out a tala, one bol to a beat. `f.tala()` plays it. [Chapter 17](17_ragas_and_talas.md#talas)
- **transform**. A change that moves, turns or resizes everything drawn after it: `f.translate()`, `f.rotate()` and `f.scale()`. [Chapter 8](08_transforms.md)

## V

- **vadi**. The most important swara of a raga. See also *samvadi*. [Chapter 17](17_ragas_and_talas.md#the-raga-table)
- **vector**. An x and a y kept together, such as a position or a speed. Made with `f.Vector(x, y)`. [Chapter 12](12_useful_maths.md#vectors)
