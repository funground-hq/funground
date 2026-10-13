# Creative Thinking Course

**A guided course in seeing, choosing and making with code**

This course helps programmers and visual makers become more deliberate designers. It teaches ways to look at images, make visual decisions, test those decisions with small experiments, and develop the strongest ideas into finished work.

It is designed to come **before funground's Studio exercises**. The course explains the ideas and gives learners their own experiments and assignments. The Studios can then serve as short follow-up studies, once learners have some experience noticing and changing visual relationships.

The course complements, rather than repeats, the [funground guide](guide/README.md). The guide explains how to use the drawing tools. This course asks what to make with them, what to pay attention to, and how to decide whether a change helped.

## Who this is for

You can begin if you can open and run a short Python sketch. You do not need to know art or design terminology. The course introduces each idea in ordinary language, then uses a little code to make the idea visible.

If you are new to funground, first follow [Getting started](guide/01_getting_started.md) and learn how to run a sketch. Keep the [guide](guide/README.md) nearby as a reference for drawing functions. You do not need to read every chapter first.

## How to use the course

Allow one or two sessions per lesson. Keep your experiments small: use a few shapes, words or movements so you can see what each decision changes.

For each lesson:

1. **Look before you make.** Describe what you notice in a poster, book cover, sign, object or image. Separate what you can see from what you think it means.
2. **Name the question.** Choose one visual problem, such as “Which part should I notice first?”
3. **Run the experiment.** Make a first version using the code or instructions below.
4. **Change one decision.** Alter position, size, colour, spacing, timing or another named variable.
5. **Compare versions.** Put them side by side. Say what changed before choosing one.
6. **Make a new piece.** Use the assignment to carry the idea into a subject of your own.
7. **Keep a note.** Record what you tried, what you noticed and what you want to try next.

A reference work is something to study, not a pattern to copy. Borrow a question or a method of looking; make your own subject, rules and visual choices.

## Lesson 1 — Look, frame and compose

### The idea

A composition is the arrangement of everything inside a frame. The frame might be a page, a phone screen, a poster or a window. A mark's position matters partly because of the space around it. Empty space is active: it can give an object room, make it feel isolated, or pull attention toward it.

Before adding detail, ask:

- What do I notice first?
- Where does my eye go next?
- What is close to the edge? What has room around it?
- If I remove one element, does the picture become clearer?

### Experiment: one circle, three readings

Run this sketch. It keeps the circle the same size and changes only its position. Read the three panels from left to right. Notice how the same mark feels different in each frame.

~~~python
import funground as f


def setup():
    f.size(720, 300)


def draw():
    f.background("#f3efe6")
    f.no_stroke()

    panel_width = 220
    panel_top = 40
    positions = [(70, 80), (110, 150), (170, 70)]

    for i, (x, y) in enumerate(positions):
        left = 20 + i * 235
        f.stroke("#c9c0ae")
        f.stroke_width(1)
        f.no_fill()
        f.rect(left, panel_top, panel_width, 220)

        f.no_stroke()
        f.fill("#e76f51")
        f.circle(left + x, panel_top + y, 44)


f.run()
~~~

The circle in the first panel sits close to two edges. In the second, it has more room and sits low. In the third, it is off-centre but not cornered. There is no universally correct position; each one suggests a different relationship to the frame.

### Try these changes

1. Keep the circle's position and make it half the size. Does the empty space feel more important?
2. Add a small dark square. Try putting it near the circle, then far away.
3. Make a 3-panel comparison in which only one thing changes between panels.

### Assignment

Make a composition from three simple shapes that suggests one of these: **quiet**, **crowded**, **unstable**, or **open**. Make three versions. Keep the shapes and colours the same; change only their arrangement. Title each version with the feeling it suggests.

### Look back

Which version gives the clearest reading? Point to the exact spacing or position that helped. If another person reads it differently, ask what they noticed first.

### Refer to the guide

[Shapes](guide/03_shapes.md) explains shape placement and coordinates. [Colour](guide/04_colour.md) lists ways to choose and apply colours.

## Lesson 2 — Visual weight, balance and hierarchy

### The idea

Some elements attract more attention than others. A large shape often feels heavier than a small one. A dark mark can feel heavier than a pale one; a bright accent can attract attention from across the page. These are visual weights.

**Balance** is how those weights feel distributed. A composition can be symmetrical, but it can also feel balanced with unlike elements on each side. **Hierarchy** is the order in which information is noticed. A poster might lead with its event name, then date, then venue.

### Experiment: balance the page

Start with a large dark circle on one side. Add a small bright mark on the other. Try changing the small mark's distance, size or brightness. Do not change all three at once.

~~~python
import funground as f


def setup():
    f.size(600, 360)


def draw():
    f.background("#f3efe6")
    f.no_stroke()

    f.fill("#264653")
    f.circle(190, 180, 150)

    f.fill("#e76f51")
    f.circle(430, 125, 46)


f.run()
~~~

Move the small circle toward the edge, then closer to the large one. Make it smaller, then brighter. Ask whether the page feels more balanced, more tense or simply different. Balance is not a formula to solve; the experiment helps you describe the effect of a choice.

### Try these changes

- Place both circles on the same side. Can unequal size still feel balanced?
- Replace the small circle with a short line or a cluster of three dots.
- Add a third element and decide which should be noticed first, second and third.

### Assignment

Design a small “notice” card with a short heading and one supporting mark. Make three versions: one where the heading dominates, one where the image dominates, and one where they share attention. Ask a viewer what they noticed first before explaining your intention.

### Look back

Did the viewer notice the intended first element? If not, which competing element took attention, and what could you change?

### Refer to the guide

Use [Shapes](guide/03_shapes.md) for marks and placement and [Text](guide/06_text.md) for text size and alignment.

## Lesson 3 — Contrast and colour

### The idea

Contrast is a visible difference: light against dark, large against small, smooth against rough, quiet against busy. Contrast can make an element stand out, but too many competing contrasts make a page noisy.

Colour is one kind of contrast. A useful first step is to separate **hue** (the colour family) from **value** (how light or dark it is). Two colours can have different hues but similar values, so text may be hard to read. A limited palette helps the parts of a design belong together.

### Experiment: test the same message in two palettes

Use the same shapes and layout in both panels. Change only the colours. Which version has clearer contrast? Which one feels warmer, calmer or more urgent?

~~~python
import funground as f


def panel(left, paper, ink, accent):
    f.no_stroke()
    f.fill(paper)
    f.rect(left, 0, 280, 260)

    f.fill(accent)
    f.circle(left + 72, 82, 56)

    f.fill(ink)
    f.rect(left + 122, 54, 116, 10)
    f.rect(left + 122, 78, 84, 10)
    f.rect(left + 42, 158, 196, 50)


def setup():
    f.size(600, 300)


def draw():
    f.background("#ded8cc")
    panel(10, "#f4f1de", "#1d3557", "#e76f51")
    panel(310, "#274c5e", "#d5e4d5", "#e9c46a")


f.run()
~~~

The bars stand in for text: the test is about which elements separate clearly from their background. When you replace them with real words, check the reading at a small size too.

### Try these changes

1. Keep the palette, but swap the ink and accent roles.
2. Make the background and ink closer in value. Notice when the bars stop being easy to see.
3. Use only two colours, then add one accent. Give that accent a job: highlight a date, button or key idea.

### Assignment

Choose a mood—**festive**, **serious**, **gentle**, or **warning**—and make two colour treatments for the same simple card. Keep the layout fixed. Write down which colour decision carries most of the mood and which information must remain readable.

### Look back

Check the design from farther away or as a small thumbnail. Does the important element still stand out? If you have a printer, compare a colour print with a black-and-white version.

### Refer to the guide

The [Colour](guide/04_colour.md) chapter covers colour values and modes. The [Text](guide/06_text.md) chapter helps check readable text.

## Lesson 4 — Shape, figure and ground

### The idea

A viewer reads a shape in relation to its background. The shape they attend to is the **figure**; the surrounding area is the **ground**. In a silhouette, the outside contour does much of the communicating. A simple shape can suggest an object or idea if its outline is distinctive and the surrounding space supports the reading.

Abstraction means keeping some features and leaving others out. It does not mean making something vague at random. Decide which feature carries the idea: outline, proportion, direction, colour or relationship to another shape.

### Experiment: how few marks are enough?

Draw a simple symbol from two or three shapes. For example, a plant might be a stem and two leaves; a house might be a roof and a doorway. Change its scale and remove one part at a time.

~~~python
import funground as f


def plant(x, y, scale, colour):
    f.no_fill()
    f.stroke(colour)
    f.stroke_width(5 * scale)
    f.line(x, y, x, y - 70 * scale)
    f.line(x, y - 38 * scale, x - 28 * scale, y - 58 * scale)
    f.line(x, y - 48 * scale, x + 28 * scale, y - 66 * scale)

    f.no_stroke()
    f.fill(colour)
    f.ellipse(x - 38 * scale, y - 68 * scale, 30 * scale, 14 * scale)
    f.ellipse(x + 38 * scale, y - 76 * scale, 30 * scale, 14 * scale)


def setup():
    f.size(600, 300)


def draw():
    f.background("#f3efe6")
    plant(150, 230, 1.0, "#264653")
    plant(300, 230, 0.7, "#e76f51")
    plant(465, 230, 1.2, "#2a9d8f")


f.run()
~~~

Compare the three plants. Does a smaller version still read as a plant? Which line or leaf could you remove without losing the idea? Try reversing the figure and ground: draw a dark background and make the plant light.

### Assignment

Create a small set of three symbols for a place, club or fictional service. Use the same visual language for all three. Show each symbol at a large and a small size, and simplify until each remains recognisable.

### Look back

Ask someone what they think each symbol means before giving them the answer. Which contour or relationship helped? Which caused a different reading?

### Refer to the guide

Use [Shapes](guide/03_shapes.md) for primitive geometry and [Paths, clipping and pictures](guide/09_paths_and_clipping.md) when you want to build or combine custom outlines.

## Lesson 5 — Repetition, rhythm and variation

### The idea

Repetition creates order. A repeated mark can also create rhythm: the eye senses a beat, pause or acceleration as size, spacing or direction changes. **Variation** makes a pattern feel alive, but too much variation can hide the rule.

A useful way to design a pattern is to choose one stable rule and one variable. For example, keep the spacing fixed and vary size; or keep size fixed and vary spacing. Code is helpful because it can repeat a mark consistently while you concentrate on the visual rule.

### Experiment: change the beat

Run the sketch and compare the rows. Each uses the same marks; the spacing changes.

~~~python
import funground as f


def row(y, gaps, sizes, colour):
    x = 40
    f.no_stroke()
    f.fill(colour)
    for gap, size in zip(gaps, sizes):
        x += gap
        f.circle(x, y, size)
        x += size / 2


def setup():
    f.size(640, 300)


def draw():
    f.background("#f3efe6")
    row(70, [24] * 8, [18] * 8, "#264653")
    row(145, [12, 24, 36, 48, 36, 24, 12, 24], [18] * 8, "#e76f51")
    row(220, [24] * 8, [10, 14, 18, 26, 34, 26, 18, 14], "#2a9d8f")


f.run()
~~~

The first row has a steady beat. The second changes the gaps. The third changes the size. You can make the pattern regular or irregular, but decide what the change should do: build energy, make a pause, point to an accent or suggest a natural variation.

### Assignment

Design a border, textile swatch or small album artwork from one repeated mark. Make three versions: steady, gradually changing and interrupted by a deliberate accent. Save the versions together so they can be compared.

### Look back

Which rule is easiest to notice? Does the accent feel intentional? If the pattern feels messy, reduce the number of things that vary.

### Refer to the guide

[Animation and time](guide/07_animation_and_time.md) and [Randomness and noise](guide/11_randomness_and_noise.md) show how repetition can extend into motion and procedural variation.

## Lesson 6 — Type, words and hierarchy

### The idea

Typography is the design of written language. A type choice can suggest a voice, but the first job of type is to let the reader find and understand the words. Size, weight, spacing, alignment and position create hierarchy.

Try reading a design at three distances: close up, at normal size and as a small thumbnail. A title that works only when enlarged may not work as a poster or cover. Use fewer type styles than you think you need; contrast between two well-chosen sizes is often enough.

### Experiment: one title, three hierarchies

Use a short phrase, such as **NIGHT GARDEN**. Make three versions: large title and small detail; title and detail at similar sizes; small title with a large visual mark. Keep the words and colour fixed.

~~~python
import funground as f


def title_card(title_size, detail_size, title_y):
    f.fill("#1d3557")
    f.text_size(title_size)
    f.text_style("bold")
    f.text_align("left", "top")
    f.text("NIGHT GARDEN", 40, title_y)

    f.fill("#e76f51")
    f.text_size(detail_size)
    f.text_style("normal")
    f.text("A small exhibition of plants after dark", 40, 210)


def setup():
    f.size(640, 300)


def draw():
    f.background("#f4f1de")
    title_card(54, 16, 55)


f.run()
~~~

Change the title and detail sizes, then move the title. To compare three versions at once, copy the card into three panels and adjust the x positions. Keep the text readable while changing emphasis.

### Assignment

Choose a short phrase and design a title card for it. Make three hierarchy studies before choosing one. Then make a second card for a different audience using the same words. What changed: the type scale, the spacing, the voice, or the supporting image?

### Look back

Cover the design and reveal it from top to bottom. What do you notice first? Ask a viewer to read the words in order. If they skip a detail you consider essential, make its role clearer.

### Refer to the guide

[Text](guide/06_text.md) explains text functions, alignment and styles. [Saving your work](guide/13_saving_your_work.md) explains exporting images and vector files.

## Lesson 7 — Make a cover

### The idea

A cover has several jobs: identify the work, signal its character, attract the intended reader and remain legible as a small thumbnail. The image and title should work together. They can explain each other, echo each other or create a useful tension.

Begin with a brief, not decoration:

- What is the book, album or zine about?
- Who might pick it up?
- What should the cover make that person expect?
- What must be readable when the cover is small?

### Experiment: image and title as partners

Choose one simple image idea and one title. Make quick thumbnails before refining anything. Try these three relationships:

1. **Image leads:** the title is quiet and the image establishes the subject.
2. **Title leads:** the words are the main image.
3. **Image and title meet:** one shape interrupts, frames or points toward the words.

Use a grid or guides to keep margins consistent. Check the cover at thumbnail size before polishing.

### Assignment

Design a cover for a real or invented book, album or zine. Produce at least six small thumbnails, choose two different directions, and refine both. Show the two covers to someone who has not read your brief. Ask what kind of work each seems to promise. Include a short note explaining which audience you chose and why.

### Look back

Does the title remain readable at a small size? Does the visual promise match the subject? If not, change the hierarchy or image relationship before adding detail.

### Refer to the guide

Use [Text](guide/06_text.md), [Paths, clipping and pictures](guide/09_paths_and_clipping.md), and [Saving your work](guide/13_saving_your_work.md) for the making and export steps.

## Lesson 8 — Poster systems and messages

### The idea

A poster competes for attention and communicates under real constraints: a viewer may see it briefly, from a distance or on a small screen. Decide what must be understood first. Then make the remaining information support that message.

A **system** is a set of choices that lets related posters belong together: a shared grid, palette, type scale, image rule or placement. Consistency makes the family recognisable; variation makes each poster specific.

### Experiment: one system, three events

Write down the fixed parts of a poster system and the parts that can change. For example:

- fixed: margins, title position, two type sizes;
- variable: event name, date, one image mark and accent colour.

Make three tiny drafts for three events. Put them side by side. If they look unrelated, strengthen one shared rule. If they look identical, give each event one purposeful difference.

### Assignment

Create a three-poster series for a real or invented event programme. Each poster must communicate the event name, date and place. Keep at least three design rules consistent and vary at least two choices to fit each event. Export a contact sheet and each poster separately.

### Look back

Can a viewer tell the posters belong together before reading them? Can they also tell which event is which? Check that every essential detail survives at thumbnail size.

### Refer to the guide

The [Text](guide/06_text.md) and [Saving your work](guide/13_saving_your_work.md) chapters support type and output. The [Projects](guide/18_projects.md) chapter contains a guided event-poster build for learners ready to work through a larger implementation.

## Lesson 9 — Motion and interaction

### The idea

Motion is a design choice. Timing, direction, distance and pause all affect meaning. A quick movement can feel sharp or urgent; a slow one can feel gentle or heavy. Stillness is also a choice.

Interaction adds another question: what can a viewer do, and what response tells them it worked? A useful interaction makes the action and its consequence understandable. A response may be movement, a colour change, a sound or a new piece of information.

### Experiment: make an element respond

Start with one object and one input. For example, make a circle follow the mouse. Then add one clear response: grow while pressed, change colour near a target, or stop at an edge. Change one response at a time and ask whether it makes the interaction easier to understand.

For motion without input, animate one property such as position or size. Compare a steady pace with a pause at the end. Use [Animation and time](guide/07_animation_and_time.md) for frame-based sketches and [Interaction](guide/10_interaction.md) for mouse and keyboard input.

### Assignment

Make a small interactive poster or visual instrument. Give the viewer one obvious action and one visible response. Ask a first-time viewer to try it without instructions. Revise the design if they cannot tell what to do or whether their action changed anything.

### Look back

What did the viewer try first? What did the system do next? Did the response feel connected to the action? Keep the interaction simple enough that the visual idea remains clear.

### Refer to the guide

Read [Animation and time](guide/07_animation_and_time.md) and [Interaction](guide/10_interaction.md). The [Projects](guide/18_projects.md) chapter links to larger interactive builds.

## Lesson 10 — Rules, chance and generative work

### The idea

A generative artwork is made with a set of rules. The maker chooses the rules, decides what may vary, and selects what to keep. Randomness can help produce alternatives, but it does not make the design decisions for you.

Use **constraints** to give the work a character. For example: only circles and lines; three colours; a fixed grid; one mark that can rotate but not change size. Change one rule and notice how the family of results changes.

### Experiment: build a small edition

Choose a mark, a page, a palette and one rule for variation. Make a set of outputs. If the results use randomness, record a seed so you can return to a version you like. Compare the outputs and select a small group that feels related without being identical.

~~~python
import funground as f


def setup():
    f.size(500, 500)
    f.random_seed(12)


def draw():
    f.background("#f3efe6")
    f.no_stroke()

    colours = ["#264653", "#2a9d8f", "#e9c46a", "#e76f51"]
    for row in range(8):
        for col in range(8):
            x = 40 + col * 60
            y = 40 + row * 60
            size = f.random(12, 42)
            colour = f.random_choice(colours)

            f.fill(colour)
            f.circle(x, y, size)


f.run()
~~~

Run it again with the same seed: the result should repeat. Then change the seed to make another version. The grid stays fixed, so you can focus on how scale and colour vary. Next, restrict the palette or use only three sizes. A rule can make the set more coherent than adding more randomness.

### Assignment

Make a collection of 12 related images from your own rules. Save the code and the outputs. Select three images for a small edition, give the edition a title, and write down why those three belong together.

### Look back

Which decisions came from your rules? Which came from your selection? If every image looks interchangeable, add a constraint. If each image looks unrelated, reduce the number of variables.

### Refer to the guide

[Randomness and noise](guide/11_randomness_and_noise.md) explains repeatable random values and smooth variation. [Saving your work](guide/13_saving_your_work.md) covers image, vector and motion exports.

## Lesson 11 — Capstone: make a small visual world

Choose a subject you care about: a place, a story, a local event, a collection, an imaginary product or a feeling. Decide who the work is for and what you want them to notice or understand.

Make a connected set of three pieces. For example, a cover, a poster and a short motion piece; a poster, an interactive screen and a set of generative variations; or three pages from a small publication.

Work through these stages:

1. **Write a brief.** Name the audience, purpose, format and one constraint.
2. **Collect observations.** Gather words, shapes, colours, textures or references that relate to the subject. Note what you notice; do not copy a finished design.
3. **Make thumbnails.** Try several different compositions before writing much code.
4. **Choose a visual system.** Define a small palette, type hierarchy, spacing rule and image approach.
5. **Build and compare.** Make one version, change a named decision, and compare.
6. **Refine.** Fix the most important communication problem first. Add detail only when it helps.
7. **Present.** Show the work at its intended size, include one early version, and explain one decision you changed.

### Capstone review

Ask a viewer:

- What did you notice first?
- What do you think this is for?
- Which pieces feel related?
- What is one part you would like to understand better?

Record the answers without defending the work immediately. Decide which feedback helps you reach your brief. The maker makes the final choice.

## A simple critique routine

Use this for assignments and the capstone:

- **I notice…** Point to something visible.
- **I read…** Say what that choice suggests or helps you understand.
- **I wonder…** Ask a question that opens a useful next experiment.
- **The maker decides…** The learner chooses what to change and records why.

Avoid comments that stop at “I like it” or “I don't like it.” Ask what in the work created that response: the colour, size, spacing, contrast, word or movement.

## Keep a small process portfolio

For each lesson, save:

- the question or brief;
- at least two versions;
- the final image, animation or recording;
- a short note on what changed and what you noticed;
- the code that made the final result.

A strong portfolio shows decisions, not just polished outcomes. An early version makes learning visible.

## After this course: continue with Studios

The Studio exercises are short follow-up studies. Try them after completing the related course lessons; they give you a focused way to revisit an idea while also learning funground's studio tools.

| Course ideas | Follow-up Studio |
|---|---|
| Composition, placement and grouping | [Studio 1: Placement](guide/19_studios.md#studio-1-placement) and [Studio 2: Proximity](guide/19_studios.md#studio-2-proximity) |
| Rhythm and repetition | [Studio 3: Rhythm](guide/19_studios.md#studio-3-rhythm) |
| Shape and visual meaning | [Studio 4: Boolean shapes](guide/19_studios.md#studio-4-boolean-shapes) |
| Type and letterforms | [Studio 5: Text as geometry](guide/19_studios.md#studio-5-text-as-geometry) |
| Poster systems | [Studio 6: A poster series](guide/19_studios.md#studio-6-a-poster-series) |

The [Projects](guide/18_projects.md) are longer guided builds. Try one when you are ready to bring several ideas together.

## Further material

These sources offer other ways into creative coding and visual design. They are prompts for further study, not templates for the course assignments.

### Books and longer reading

- [Foundations of Digital Art and Design with Adobe Creative Cloud, 2nd edition](https://learning.oreilly.com/library/view/foundations-of-digital/9780135711965/) — a broad introduction to digital art and design.
- [Coding Art: The Four Steps to Creative Programming with the Processing Language](https://learning.oreilly.com/library/view/coding-art-the/9781484262641/) — a project-based way to connect programming and visual ideas.
- [Code as Creative Medium](https://mitpress.mit.edu/9780262542043/code-as-creative-medium/) — activities and teaching approaches for creative coding.

### Video

- [p5.js creative coding projects](https://www.youtube.com/watch?v=o5t7PxRJSXk) — watch selected sections and ask what design idea each project explores:
  - 01:00 — rotating blocks and interaction;
  - 28:17 — trigonometry as a source of visual form;
  - 43:48 — kinetic typography;
  - 1:10:13 — hypnotic flowers;
  - 1:29:06 — a Mondrian-inspired generative composition.

### In the funground documentation

- [The guide](guide/README.md) for drawing and coding techniques.
- [Projects](guide/18_projects.md) for longer builds.
- [The examples gallery](gallery/README.md) for seeing a feature in a small sketch.
