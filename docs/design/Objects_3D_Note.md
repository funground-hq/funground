# From sketch to object: a 3D model of our own?

**Status:** a study for the maintainer, 6 November 2026 (E-41). Nothing here is decided: the direction is D-133. No 3D code
exists. Claims about other tools come from their documentation or from memory, are not measured, and are marked
**unverified** where they matter. Spike S-265 is the test.

## The question

funground records what a sketch asks for in a backend-neutral IR (`funground/ir.py`), and Cairo turns that into a screen, a
PNG, a PDF or an SVG. Could the same idea work in 3D: our own representation, written out to Blender, OpenCascade (through
build123d), OpenSCAD and others? And what would that be worth?

This is a different thing from E-21. E-21 draws 3D on the screen in real time, with cameras, lights and shaders. The
Architecture Review called that "a 3D engine in all but name". This note is about making **files of objects**: things to
print, cut, model further or render.

## The short answer

Yes, for a small part of 3D, and that small part is where funground has something to add.

- **The value is not "one model for all 3D tools".** A general one is not possible (see below), and adults who want CAD are
  better served by build123d or OpenSCAD directly.
- **The value is a door from 2D drawing into making things.** A learner who can draw a shape, repeat it and seed it can
  get a real object, in the same language, without learning CAD first. funground's strength is the 2D profile: type,
  booleans, noise, imported SVGs.
- **The best form of it may be writing code, not files.** The model can write an OpenSCAD file, a build123d script or a
  Blender script as plain text. That needs no 3D library at all, and the learner gets a readable next step into a real tool.

## Why 3D is harder than 2D here

The 2D plan works because PDF, SVG and Cairo share one idea of a picture: paths, fills and strokes. 3D tools do not share
one idea of an object:

| Tool | What an object is | Strong at | Weak at |
|---|---|---|---|
| OpenCascade, build123d | Exact surfaces and edges (BREP) | Fillets, engineering parts, STEP files | Install size; speed of previews |
| OpenSCAD | A tree of solids, resolved to a mesh | Simple, repeatable parts for printing | Fillets; organic shapes |
| Blender | An editable mesh with modifiers | Pictures, animation, materials, sculpting | Exact dimensions; clean solids |
| glTF, STL, 3MF | A finished mesh | Moving objects between tools | Holds no history: it cannot be edited as a design |

So a shared model only covers what all of them can do: **primitives, moves, booleans, and extruding or revolving a
profile.** Above that line nothing carries across:

- **Rounding an edge** needs a way to name the edge. Names of edges change when a model changes, the "topological naming
  problem" of CAD, and a mesh tool has no such names at all.
- **The same shape differs:** a circle is exact in OpenCascade and a polygon in OpenSCAD, unless the number of sides is
  chosen for it.
- **Booleans behave differently** when faces touch exactly, which is what beginners draw.

This is the real limit. Export is one way, and the model stays deliberately small.

## What it would give

| Benefit | For whom | Why it matters |
|---|---|---|
| One language from 2D to 3D | Learners | The same `f.` thinking: loops, `random_seed`, sliders. No new tool to learn before the first success |
| Real objects from sketches | Learners, classes | A rangoli becomes a coaster, a name becomes a stamp. Making a thing holds attention in a way a screen does not |
| No heavy engine in the sketch | Everyone | The model is plain data, so a sketch stays light. Only the step that makes a mesh needs an engine, and that can be another program |
| A readable next step | Learners who grow | Written code shows what a real tool does: the learner leaves funground for build123d or Blender with something that works |
| Choice by purpose | Makers | The same design goes to printing, to engineering (STEP) or to a render (Blender) |
| A sketch outlives a tool | Everyone | Backends can change while sketches do not, as they did in 2D |
| Testable and easy for assistants | Maintainer, AI tools | Plain data can be snapshotted. A small, documented vocabulary is far easier for an assistant to write correctly than CAD |
| Variations of objects | Learners, designers | Seeds and sliders give families of objects, which is hard work in a CAD window |

The first and the second are the reasons to do it. The others are welcome, but none would justify it alone.

## What it would cost

- **Seeing the object.** This is the largest cost. A learning tool must show the result while you work, and exporting to
  another program does not give that. The choices are a viewer on the web page (three.js), or a simple shaded view drawn
  through funground's own 2D IR. Either needs a mesh, so an engine comes back in by this door. **Unsolved.**
- **Installing another tool.** Opening a `.scad` file needs OpenSCAD. That is a real step for a child on a school computer.
- **A contract for each writer.** "The same object" must be defined. Pixel goldens will not do: a test compares bounding
  boxes and volumes within a tolerance. Each writer is maintained against a tool that changes.
- **Pressure to grow.** People will ask for fillets. The answer has to stay no, or the model becomes a poor CAD program. The
  capability registry (E-07) is the existing pattern: an unsupported feature fails with a message that names the tool that
  has it.
- **Units.** `f.mm()` gives points, because the canvas is in points, while 3D tools work in millimetres. A writer must
  convert, or it repeats the SVG unit bug (S-260).

## Options

| Option | What it is | Gain | Cost |
|---|---|---|---|
| A. Keep current behaviour | SVG out, then the learner's own tool | Nothing to build; a guide project is enough | No shared language; 2D only |
| B. A bridge to one engine | A separate package: funground paths become build123d shapes | Exact curves, all of build123d | Tied to one heavy engine |
| C. A small model of our own | A separate package with a few kinds of object, and writers for several tools | Everything in the table above | The costs above, most of all the viewer |
| D. 3D in the core | E-21 in full | Real-time 3D in sketches | Larger than everything so far; rejected for now by D-014 and ADR-003 |

## Recommendation

Do this in steps, and let each step earn the next:

1. **Now:** fix the SVG unit (S-260), because everything below depends on true sizes.
2. **S-264:** a spike taking an SVG through build123d to an STL. It is cheap, needs no funground code, and it may become a
   guide project on its own.
3. **S-265:** a spike of the small model with three text writers, with its pass/fail set in advance. It shows whether option
   C is real or only attractive.
4. **Decide D-133** with those numbers. Build S-266 only if learners want it and the viewer has an answer.

Nothing goes into the core. Under ADR-007 this is a separate package, and the rule that the same file runs on a computer and
in the browser still holds. No part of this is before 1.0.

## What was checked, and what was not

- **build123d in the browser:** an earlier reply in this work said it probably could not run there. That was wrong. The
  [OCP.wasm](https://github.com/yeicor/OCP.wasm) project ports what build123d needs to run under Pyodide. Its README warns
  that speed and support vary by browser. Not tried here.
- **build123d:** BREP modelling on OpenCascade, Apache-2.0 ([documentation](https://build123d.readthedocs.io/en/latest/external.html)).
  Install size **unverified**: S-264 measures it.
- **manifold3d:** a mesh boolean library, a Python package and an npm WebAssembly build
  ([PyPI](https://pypi.org/project/manifold3d/)). Whether the Python package loads in Pyodide is **unverified**. It may be the
  light engine that a viewer needs.
- **Does this exist already?** One search found no library that writes both OpenSCAD and build123d from a shared model. One
  app that supports both says that it does not translate between them
  ([Torrify](https://torrify-website.pages.dev/docs/features/CAD_BACKENDS)). That is weak evidence of a gap: it could equally
  mean that the idea is hard. SolidPython, which generates OpenSCAD from Python, is the nearest relative from memory and
  did not appear in that search. Look harder before S-265.
- **The maintainer's machine** has no OpenSCAD or Blender, and installers are not run there. S-265 needs a cloud sandbox for
  those two; build123d can be installed in a virtual environment.

## Rejected for now

- **Importing from 3D tools.** One way only: a round trip would need the whole of each tool's model.
- **Blender through `bpy`.** A generated script or a glTF file needs nothing in the learner's sketch; `bpy` is a very large
  dependency.
- **A mesh of our own.** Writing our own mesh booleans is the reimplementation that the Architecture Review warned against.
