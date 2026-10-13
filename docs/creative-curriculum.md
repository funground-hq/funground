# A creative curriculum for funground

**Purpose:** help programmers and visual makers become more deliberate, curious designers by making images, motion and interactive work with code.

This is a design-led course map, not a second set of examples. Each unit starts with a visual question and uses the code needed to explore it. Where funground already has a suitable studio or project, the course reuses it and adds a design lens or reflection; new briefs fill gaps in the current collection.

## Who it is for

The path is for beginners who can read and change short Python sketches, as well as artists and designers who are new to programming. A learner can begin with the first studios and take the later studios at a slower pace. Instructors can run it as a 12–16 week course, a series of workshops, or a self-guided set of projects.

A short orientation to Python variables, function calls, `setup()`, `draw()`, and running a sketch is enough to start. New language features are introduced in context: coordinates, values, functions, loops, conditionals, lists and dictionaries. The visual goal stays in front.

## What learners will be able to do

By the end, learners can:

- arrange visual elements with intention, using scale, position, balance, contrast, rhythm and negative space;
- choose and apply colour and type for a purpose;
- use grids, repeated marks and constraints to create a family of related images;
- make a cover or poster that communicates through image and hierarchy;
- use time, input and sound as parts of a visual composition;
- make a generative artwork whose variations are both surprising and considered;
- explain what they changed, what they noticed, and why they kept a version;
- export work appropriately for screen, print or motion.

## The studio loop

Use the same loop throughout. It makes design decisions visible and gives code a reason to exist.

1. **Notice:** look at an image, object, place or piece of typography. Name one thing you see before explaining what you think it means.
2. **Frame:** choose a question and a constraint. For example: “How many ways can the same three shapes feel balanced?”
3. **Make:** build a small first version. Keep the number of new ideas and new API calls low.
4. **Vary:** change one decision at a time, or make a deliberate set of alternatives.
5. **Compare:** put versions side by side. Describe differences before choosing a favourite.
6. **Keep and explain:** save the chosen version and write a short note about the decision.

A studio is not a race toward a polished sample. The reference image, if one is used, is a prompt for observation, not a template to reproduce. Learners should make their own subject, rules and visual choices.

## The learning path

Each studio takes one or two sessions. The core task should fit in one session; the extension can become a second session or homework.

| Studio | Design question and ideas | Make | Code that earns its place |
|---|---|---|---|
| 1. A page with a point of view | Where does the eye go first? Composition, frame, figure and ground, scale, balance, negative space | A three-shape composition in three arrangements | Page size, coordinates, shapes, colour, variables |
| 2. One mark, many relationships | How does a mark change when it moves? Placement, proximity, grouping, alignment | A contact sheet showing one mark in nine positions and a second sheet showing different groupings | Functions, loops, grids, reusable marks |
| 3. Rhythm and pattern | What makes repetition feel steady, playful or tense? Rhythm, interval, repetition, variation | A patterned page using one shape and one controlled variation | Nested loops, parameters, transforms |
| 4. Colour with a job | How does colour change emphasis and mood? Hue, value, saturation, contrast, limited palettes | Three versions of the same composition for three different moods | Named colours, palette data, HSB/HSL, iteration |
| 5. Shape and the space around it | Can empty space become the subject? Silhouette, edge, overlap, positive and negative space | A bold two-colour image built from a few combined or cut-out shapes | Paths, clipping and boolean shapes where useful |
| 6. Type as image | What can a word communicate before it is read? Typographic scale, weight, alignment, spacing, hierarchy | A one-word type study, then a small title card | Text, alignment, size, style, text measurements |
| 7. A cover that invites a reader | How do image, title and small details work together? Grid, hierarchy, margins, image-text relationship | A book, album or imaginary publication cover, with a second edition or alternate cover | Images or paths, text, reusable layout functions, print page sizes |
| 8. A poster that belongs to a series | What stays consistent, and what changes? Information hierarchy, contrast, visual identity, systems | Three event posters sharing a visual rule but serving different events | Data-driven content, functions, palette and type systems, PDF/SVG export |
| 9. Motion with intention | What should move, and what should stay still? Timing, anticipation, repetition, trajectory, kinetic type | A short looping title or shape animation; export a GIF or frame sequence | `draw()`, time, state, transforms, motion export |
| 10. An artwork that listens to a person | What can a viewer do, and what response makes sense? Affordance, feedback, agency, interaction | An interactive display in which pointer or keys change a visual rule | Mouse/keyboard input, conditionals, controls, state |
| 11. Rules, chance and a collection | How can chance produce variety without losing the idea? Constraints, seed, systems, emergence, authorship | A set of 6–12 related generative prints; select and title a small edition | Randomness, noise, seeds, loops, reusable rules, saving |
| 12. Capstone: a small visual world | How can the parts support one clear intention? Selection, refinement, consistency, presentation | A self-directed project: cover, poster family, interactive artwork, motion piece or generative collection, with a short process note | Learner chooses the tools; organize, refine, export and explain |

### Stretch path

Learners ready for more can add a second input, make a responsive layout, use image pixels, build a multi-page PDF, map sound to a visual feature, or create a small tool with controls. These are extensions, not prerequisites for the core sequence.

## A light critique, every time

Use a short, repeatable critique so feedback stays specific and useful:

- **I notice…** Describe a visible choice without judging it.
- **I read…** Say what that choice makes you expect, feel or understand.
- **I wonder…** Ask a question that might help the maker decide what to try.
- **The maker decides.** The learner chooses whether to use the suggestion and records why.

Ask learners to compare versions by naming the changed variable: “The title became easier to find when I increased its size and gave it more empty space.” Avoid treating personal taste as a universal rule.

## Evidence of learning

Keep one small portfolio entry for each completed studio:

- the brief or question;
- two or more variations, including an early version;
- the final image or recording;
- a short note: what changed, what the learner noticed, and what they would try next.

Assess the evidence on four dimensions, with beginner-friendly expectations:

1. **Intention:** can the learner say what the work is trying to do?
2. **Visual decisions:** can they point to choices about hierarchy, spacing, colour, rhythm or motion?
3. **Iteration:** did they make and compare alternatives, rather than stop at the first output?
4. **Code and craft:** does the sketch run, and can the learner find and change the rule behind a visual result?

There is no single correct style. A simple, intentional piece can show stronger learning than a complex sketch whose choices the maker cannot explain.

## Mapping to the repository

The course uses the existing guide and examples as references, not as a required sequence of API lessons:

- Begin with [Getting started](guide/01_getting_started.md), [The sketch](guide/02_the_sketch.md), [Shapes](guide/03_shapes.md), and [Colour](guide/04_colour.md).
- Use the [Studios chapter](guide/19_studios.md) alongside studios 1–3. Its placement, proximity, rhythm, Boolean-shape, text-as-geometry and poster-series exercises already model the compare-and-choose habit.
- Pull examples from the [gallery](gallery/README.md) when a learner needs to see one capability in isolation.
- Use [Projects](guide/18_projects.md) after the related studios. Event posters, rangoli, typographic portraits, kinetic type and flow-field prints are natural extensions.
- Refer to the chapters on [animation](guide/07_animation_and_time.md), [interaction](guide/10_interaction.md), [randomness and noise](guide/11_randomness_and_noise.md), [saving](guide/13_saving_your_work.md), [sound](guide/16_sound.md) and [useful maths](guide/12_useful_maths.md) when those ideas enter a project.

This curriculum works with the current desktop workflow and exported image, vector, document and motion formats. Its studio prompts can also be delivered through a browser editor when that workflow is available; no browser-specific step is required to learn the design ideas.
