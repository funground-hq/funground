# Spike S-225: how renowned books lay out their pages

A study to guide the page system of a funground book. It looks at ten books (one is a family of books), says what each
does with its pages, and says what funground takes and what it leaves. It ends with principles and open questions.

**The book being planned** (the maintainer's answers, 18 Oct 2026). The reader is starting to learn programming and is
drawn in by colour and shape. The book should break the idea that programming is mostly mathematics. It is a PDF first,
with print as the ambition, so bleed and a trim are planned from the start. Its pictures are hand-drawn, in the manner of
children's picture books. Chapter 1 draws shapes of different colours with no x and y. Chapter 2 makes shapes meet
(union, difference, intersection), then adds filters. The material already exists in funground's guide chapters, gallery
examples (each with its picture), step-by-step projects such as `docs/guide/projects/11_moving_the_paper.md`, and the
course's Predict / Run / Compare / Extend steps (`examples/course/`, `docs/course/`).

**How to read this.** Where a claim comes from a source, the source is linked. Where I describe a page that no source
I found describes, I mark it *(unverified)*: it comes from memory of the book and should be checked against a copy
before anyone relies on it. Following D-026, nothing here describes an illustration so that it could be imitated. We
take principles, not looks.

## The books, and why each was chosen

| # | Book | Kind | Why it is here |
|---|---|---|---|
| 1 | Josef Müller-Brockmann, *Grid Systems in Graphic Design* (1981) | grids | The standard account of a modular grid: one structure that serves very different pages. |
| 2 | Robert Bringhurst, *The Elements of Typographic Style* (1992) | typography | The standard account of page proportion, margins and the text block. |
| 3 | Edward Tufte, *Envisioning Information* (1990), with the Tufte layout | information design | Small multiples and side notes: how to put a picture and its explanation side by side. |
| 4 | John Maeda, *Design by Numbers* (1999) | design and code | An early book that taught artists to program on a small, fixed canvas, with code and picture together. |
| 5 | Lauren McCarthy, Casey Reas and Ben Fry, *Getting Started with p5.js* (2015) | design and code | The nearest book to funground's purpose: a short beginners' book for visual coding. |
| 6 | Bohnacker, Gross, Laub and Lazzeroni, *Generative Design* (2009; English 2012) | design and code | The best-known designed book of code: code, notes and picture woven on one page. |
| 7 | Hervé Tullet, *Press Here* (2010) | children's, interaction | Teaches cause and effect with three coloured dots and the page turn. Closest in spirit to Predict / Compare. |
| 8 | Leo Lionni, *Little Blue and Little Yellow* (1959) | children's, shape and colour | Abstract shapes that mix colour where they overlap: the subject of our Chapter 2. |
| 9 | Bruno Munari, the *libri illeggibili* and *prelibri* | children's, the book as object | Treats the page itself (its cut, its paper, its turn) as the thing that teaches. |
| 10 | Linda Liukas, *Hello Ruby: Adventures in Coding* (2015) | children's, code | The best-known picture book about programming, and a warning as well as a model. |

I left out Eric Carle. His books are famous for pages cut to different widths and holes through them, but Munari covers
the same lesson (the page as object) more directly, and Carle's look is so recognisable that it is a risk under D-026.
*Form+Code* (Reas, McWilliams, LUST) was a candidate; it is more of an essay with pictures, and *Generative Design* is
the stronger lesson for code on a page.

---

## 1. Müller-Brockmann, *Grid Systems in Graphic Design*

**What its layout does.** The book is 21 x 30 cm, 176 pages, bilingual (English and German), published by Niggli
([Thames & Hudson listing](https://thamesandhudson.com.au/?p=93182);
[Exclusive Books listing](https://exclusivebooks.co.za/products/9783721201451)). It gives directions for grids from 8 to
32 fields, and for three-dimensional work; its own cover sets the two titles, the author and the publisher in a grid of 32
fields ([Exclusive Books](https://exclusivebooks.co.za/products/9783721201451)). A review says the book is organised
"methodically, much like the grid systems it describes", moving from theory to applications to examples, with plain prose
and many diagrams ([The Art Bog](https://theartbog.com/book-review-grid-systems-in-graphic-design-by-josef-muller-brockmann/)).
Inside, the method ties the height of each grid field to whole lines of text, with a gap of one empty line between fields,
so that a picture's top and bottom line up with lines of type *(unverified: from memory of the book)*.

**What it teaches about pages.** A grid is not a look. It is an agreement that lets many different pages feel like one
book. The fields are measured from the text (its size and its line spacing), not from the paper alone.

**What funground takes.** A modular grid, chosen once for the whole book, with field heights measured in lines of body
text. Every spread (code, picture, steps) is built from the same fields. This matters for a book generated by a program:
the grid becomes a few numbers in the page system, and every gallery picture can be scaled to a whole number of fields.

**What it leaves.** The Swiss severity: ranged-left sans serif, no ornament, strict asymmetry. Our reader is drawn in by
colour and play, and a cold page would say "this is technical". We keep the structure and let the hand-drawn pictures
break across it on purpose, the way a picture book lets a picture run to the edge.

## 2. Bringhurst, *The Elements of Typographic Style*

**What its layout does.** The book's chapter on page shape and margins collects 27 examples of classical page
proportions ([Blaze Type](https://blazetype.eu/blog/the-elements-of-typographic-style)). Bringhurst's claim is that the
proportions useful for the shape of the page are equally useful for the shape and position of the text block
([Canons of page construction](https://en.wikipedia.org/wiki/Canons_of_page_construction)). He compares space in
typography to time in music. Some readers find the proportion chapter close to numerology
([Goodreads](https://www.goodreads.com/book/show/44735);
[Hacker News](https://news.ycombinator.com/item?id=1128631)). His advice on vertical space, that it should be added in
measured intervals of the line, is summarised at [webtypography.net](https://webtypography.net.clagnut.com/2.2.2). The
book's own pages have a wide outer margin that carries notes and the section numbers *(unverified)*.

**What it teaches about pages.** The text block is a shape inside a shape. Margins are not leftovers: the inner margin is
smallest, the outer and bottom larger, so a spread reads as one object. A comfortable line holds about 45 to 75
characters *(Bringhurst's guidance as it is commonly quoted; unverified against the book)*.

**What funground takes.** Measured vertical space (every gap a whole number of lines, which matches Müller-Brockmann).
Margins that make the spread one object, with room left in the gutter for binding when it is printed. A short measure
for prose, because our reader is new to reading code and will not tolerate long lines of explanation.

**What it leaves.** The search for a "perfect" page ratio. The trim will be set by printers' standard sizes and by the
pictures (see the open questions), not by a musical interval. We also leave the book's density: it is a reference for
typographers, and our book has one idea per spread.

## 3. Tufte, *Envisioning Information*, and the Tufte layout

**What its layout does.** The book has six chapters, among them "Layering and Separation" and "Small Multiples"; it has
about 400 illustrations, printed in 6 to 12 colours, and reviewers praise it as an object to hold
([Gary Sieling's review](https://www.garysieling.com/blog/author/gary/page/684/);
[Powell's](https://www.powells.com/biblio/1-9780961392116-40)). Tufte's later books, and the layout made from them for the
web, use a wide outer margin for side notes, margin notes and small figures, so a note or picture sits beside the words
that discuss it, and a figure can also span the full width when it needs to
([Tufte CSS](https://edwardtufte.github.io/tufte-css/); [Tufte-LaTeX book template](https://latextemplates.com/template/tufte-book)).
The Tufte CSS page itself warns that it is a starting point, "not print".

**What it teaches about pages.** Two ideas. *Small multiples*: show the same picture several times with one thing
changed, at the same size, in a row, so the eye does the comparison. *Adjacency*: a note belongs beside what it explains,
not at the foot of the page or on the next one.

**What funground takes.** Small multiples are already in funground: `f.variations` lays out versions side by side with a
label each, and the course's Extend sketches use it (`examples/course/README.md`). A "Compare" panel in the book is a
small multiple: three or four pictures, same size, one change each. Side notes become the place where the book explains a
single line of the code beside it.

**What it leaves.** The scholarly tone and the very wide margin on every page. Tufte's reader is an analyst; ours is a
beginner who needs big pictures. We use a margin column on code spreads, not on every page.

## 4. Maeda, *Design by Numbers*

**What its layout does.** Design By Numbers (DBN) was a language and teaching experiment from the MIT Media Lab, made to
help "designers, artists, and other non-programmers" start programming
([Wikipedia](https://en.wikipedia.org/wiki/Design_By_Numbers)). MIT described the book as a tutorial on both the
philosophy and the techniques of programming for artists, and said Maeda produced it with a computational process he built
for the purpose ([MIT News, 1999](https://news.mit.edu/1999/maeda-0512)). The language draws on a small square canvas of
100 by 100 points in shades of grey, and the book shows a short program beside the picture it makes, at a small fixed
size, many times over *(unverified: from memory of the book and the DBN software)*.

**What it teaches about pages.** A small, fixed canvas makes every picture comparable, and a page of them becomes a set
of experiments. Restriction (grey only, one size) keeps attention on the idea. And a book about programming can itself be
made by a program.

**What funground takes.** One canvas size for the early chapters, so every picture on a spread is the same shape and the
reader compares like with like. The book made by funground itself, as the maintainer intends: the page system is code, and
each picture is the output of the sketch printed beside it.

**What it leaves.** The grey. Maeda removed colour to focus on number; our reader comes for colour, and our book must not
look like mathematics. We also leave the coordinates: Chapter 1 has no x and y, so our early pages show no axes and no
numbers on the canvas.

## 5. McCarthy, Reas and Fry, *Getting Started with p5.js*

**What its layout does.** A short book (about 246 pages) published by Maker Media in 2015, with illustrations by Taeyoon
Choi ([p5.js books page](https://archive.p5js.org/books/);
[MIT Press Bookstore](https://mitpressbookstore.mit.edu/book/9781457186776)). Readers describe it as a gentle book for
someone new to programming ([Goodreads](https://www.goodreads.com/en/book/show/26451798-getting-started-with-p5-js)).
Its pages are a single column. Each idea is a numbered example: a sentence or two, the full program, then the picture it
makes, small, below the code. Chapters end with a running project that grows one step per chapter *(unverified: from
memory of the book; no source I found describes its pages)*.

**What it teaches about pages.** Numbering every example lets prose, code and download all refer to the same thing. A
complete program on the page (not a fragment) means the reader can type exactly what they see. A project that grows
across chapters gives the book a spine.

**What funground takes.** Complete sketches on the page, always, as the gallery already does ("Each example is a complete
sketch: copy it into a file and run it", `docs/gallery/README.md`). A label for each sketch that names its file, so the
reader can open it in Play. The growing project: our projects already work in steps (`11_moving_the_paper.md` has eight,
each a complete sketch).

**What it leaves.** The small picture under the code. In a technical paperback the code is the hero and the picture is
proof. For our reader the picture is the reason to read, so it is large, and the code serves it. We also leave the plain
technical-manual typography.

## 6. Bohnacker, Gross, Laub and Lazzeroni, *Generative Design*

**What its layout does.** 474 pages in the English edition (Princeton Architectural Press, 2012), translated from the
German *Generative Gestaltung* ([Masaryk University record](https://is.muni.cz/publication/1196270?lang=en)). Its book
design is credited to Julia Laub ([onformative](https://onformative.com/work/book-generative-gestaltung)). It opens with
about 160 pages of showcase work in double-page spreads; the rest is walkthroughs of sketches in which code, annotations
and pictures are "integrated closely on the page", and the code lives on a companion website
([CreativeApplications.Net](https://www.creativeapplications.net/review/generative-design-a-computational-design-guidebook/);
[Eye](https://eyemagazine.com/review/article/source-code-for-a-design-revolution)). One reviewer noted that few of the
showcase projects connect to practice ([vvvv](https://vvvv.org/blog/2010/book-review-generative-gestaltung)). Each
sketch has a short code (a letter and numbers) that ties the page to the file, and a spread shows several outputs of one
sketch alongside the lines of code that matter *(unverified: from memory of the book)*.

**What it teaches about pages.** Code can be beautiful on a page if it is set as part of the design, not dropped in as
a grey box. Show the key lines and annotate them; put the full file elsewhere. Showing many outputs of one program
proves that the program is a *system* that makes pictures, not a picture.

**What funground takes.** Annotated code: a line of code with a short note beside it. Several outputs of one sketch on a
spread (random place, random colour), which is exactly what Chapter 1 teaches. A sketch code that matches the gallery and
course file names.

**What it leaves.** Excerpted code. Our reader is a beginner and our sketches are short; the whole sketch fits, so we
print it whole. We also leave the inspiration-first structure: 160 pages of other people's work before any code would
lose our reader. Our book shows its own pictures, made by the code on the page, from the first spread.

## 7. Tullet, *Press Here*

**What its layout does.** Published in 2010; three dots, yellow, red and blue
([Publishers Weekly](https://www.publishersweekly.com/9780811879545)). A review describes the opening: one yellow dot in
the centre of a white page and the words "Press here". Each turn adds or changes dots; readers tap, tilt, shake and blow,
and on the next page the dots have scattered, grown or slid to one side
([Kirkus](https://kirkusreviews.com/book-reviews/herve-tullet/press-here/print)). It has been translated into more than
thirty languages ([Publishers Weekly](https://www.publishersweekly.com/pw/by-topic/childens/childrens-book-news/article/56875-press-here-creator-herv-tullet-takes-his-newest-project-on-tour.html)).
Tullet says he does not test his books and is surprised by children's reactions; he describes his vocabulary of dots and
scribbles as one that children share ([The Children's Book Review](https://www.thechildrensbookreview.com/qa-with-herve-tullet-yes-it-rhymes/)).

**What it teaches about pages.** The page turn is a "run" button. An instruction on one page, the result on the next,
and the gap between them is where the reader guesses. It also shows how far a white page and three colours go: nothing
competes with the idea.

**What funground takes.** This is the most important book in the study for us, because it *is* Predict / Run / Compare
without a computer. The instruction sits on the recto (right-hand page); the reader guesses; the turn reveals. Our
Chapter 1 has the same opening shape: one shape, in the centre by default, no coordinates. A plain ground (one colour, lots
of space) for the early spreads.

**What it leaves.** The fiction that the book responds to the reader (pressing does nothing; the reader's play makes it
work). Our book does respond, in Play, so we never pretend. We also leave its look entirely: no dots-on-white homage. We
take the mechanism, the turn as reveal, not the picture.

## 8. Lionni, *Little Blue and Little Yellow*

**What its layout does.** Lionni was art director of *Fortune* when he made it (1959). It began as torn paper on a
briefcase for his grandchildren and became his first picture book
([Smithsonian](https://www.smithsonianmag.com/arts-culture/smithsonian-notable-books-for-children-1997-146248536/);
[Publishers Weekly](https://www.publishersweekly.com/pw/by-topic/childens/childrens-book-news/article/74918-leo-lionni-s-unfinished-business.html)).
The characters are shapes with no faces or detail; buildings, landscape and feeling come from contour and grouping; two
colours make a third where they overlap. Lionni wanted to keep the handmade quality and avoid a machine-made look
([Untapped](https://untappedjournal.com/stories/leo-lionni-little-blue-little-yellow-graphic-design)). The text is a
short line set apart from the shapes, low on the page, with large plain grounds *(unverified)*. Publisher page:
[Penguin Random House](https://penguinrandomhouse.ca/books/101934/little-blue-and-little-yellow-by-leo-lionni).

**What it teaches about pages.** Abstract shapes can carry a story and a feeling if the page gives them room. Overlap is
an event. The rough edge of a hand-made shape makes abstraction warm.

**What funground takes.** The principle that our Chapter 2 is a story of shapes meeting. Union, intersection and
difference are not set operations here; they are what happens when two shapes meet. The page should give the meeting
room (one meeting per spread). And the warmth of an imperfect edge, which supports the hand-drawn manner (see the
synthesis).

**What it leaves.** Torn paper as a look, and any story of characters. We will not tear shapes or tell a friendship
tale; D-026 forbids imitation, and the lesson is the principle (abstract shapes, room, warmth), not the medium.

## 9. Munari, the *libri illeggibili* and *prelibri*

**What their layout does.** From the late 1940s Munari made wordless "illegible books" of papers of different colour,
texture and size, sometimes cut and sewn; some were shown at MoMA in 1955 and nine are in its collection
([London Book Arts](https://londonbookarts.org/products/libro-illeggibile-mn-1-by-bruno-munari);
[MassArt artists' books](https://blogs.massart.edu/artistsbooks/?p=6600)). One has transparent pages whose lines make new
signs as they turn; the theme throughout is reading as a creative act rather than a passive one
([Hyperallergic](https://hyperallergic.com/book-designs-that-approach-reading-as-a-creative-act)). The *prelibri* are
twelve small books for very young children, in card, cloth, plastic, wood and sponge, with no words and no drawings,
bound by hand ([Nostrofiglio](https://www.nostrofiglio.it/bambino/prelibri-di-bruno-munari-come-si-usano-e-a-cosa-servono)).
The Corraini edition of *Libro illeggibile MN 1* is 10 x 10 cm
([Idea Books](https://www.ideabooks.nl/9788886250153-bruno-munari-libro-illeggibile-mn-1)).

**What they teach about pages.** The book is an object, and the page turn, the size and the paper are part of the
lesson. A page can be read without words. Learning is something the reader does, not receives.

**What funground takes.** The reader as maker: every spread ends with something for the reader to do, and the book's
last page of a chapter is left for the reader's own work (a blank canvas frame with a prompt). Transparency as an idea:
a later edition, or a printed insert, could show two shapes on a tracing-paper overlay for Chapter 2 (an option for
print, not for the PDF).

**What it leaves.** The craft production. Die-cuts, mixed papers and hand binding are expensive and do not survive as a
PDF. We take the attitude, not the object.

## 10. Liukas, *Hello Ruby: Adventures in Coding*

**What its layout does.** About 112 pages, chiefly in colour, written and drawn by Liukas
([Iowa City Public Library record](https://search.icpl.org/Record/1466639);
[Kirkus](https://www.kirkusreviews.com/book-reviews/linda-liukas/hello-ruby/)). It began on Kickstarter, is published in
almost 40 languages ([Hello Ruby](https://www.helloruby.com/books)), and teaches without a computer. Its structure is a
story first (character pages, then a quest), then a second half of exercises, some of which refer back to the story
([Kirkus](https://www.kirkusreviews.com/book-reviews/linda-liukas/hello-ruby/)). Kirkus's verdict: "Ditch the anemic
story and nerd-pandering, but keep the nifty activity book." A reader noted that the exercises seldom connect to how
things apply, and the story never does ([Goodreads](https://www.goodreads.com/book/show/23310759)).

**What it teaches about pages.** Two lessons, one positive, one a warning. Positive: an activity page (cut, fold, draw,
sort) makes an abstract idea physical, and a friendly drawn world lowers the fear of "computers". Warning: separating
story from practice (story in the front, exercises at the back) means neither supports the other, and in-jokes for
programmers exclude the real reader.

**What funground takes.** Off-screen activities beside on-screen ones: "draw what you think this sketch will make" is a
Predict activity on paper. A drawn, friendly world.

**What it leaves.** The split structure, and any story that has to carry the concepts. In our book the activity and the
explanation share every spread. And no jokes that only programmers get.

---

## Synthesis: principles for the funground book's pages

1. **The picture leads; the code serves it.** On every spread the picture is larger than the code. This reverses the
   technical book (*Getting Started with p5.js*) and follows the picture book (*Press Here*, Lionni). It is the first
   thing that tells our reader this is not mathematics.

2. **One idea per spread.** A spread is the unit of the book, as in a picture book. Chapter 1's spreads are each one
   change: shape, colour, size, stroke. Chapter 2's are each one meeting. (*Press Here*, Lionni, Bringhurst's restraint.)

3. **The page turn is the Run button.** Predict on the recto; the reader turns; the result and Compare on the next
   verso. The gap between prompt and result is built into the paper. (*Press Here*; the course's Predict / Run / Compare.)

4. **Compare as small multiples.** Variations are shown at the same size, in a row, with one change each and a short
   label. funground's `f.variations` makes these panels, so the book uses the library's own tool. (Tufte; *Generative
   Design*; Maeda.)

5. **The whole sketch, always, and it made the picture beside it.** No fragments. The page system runs the sketch and
   places its output, so the two can never disagree, and each sketch carries a label matching its file in Play.
   (*Getting Started with p5.js*; Maeda's book made by a program; the gallery's rule.)

6. **Notes beside the line they explain.** A short note in the margin column next to the code line, not a paragraph
   below. Two to four notes per sketch. (Tufte's side notes; *Generative Design*'s annotations.)

7. **One grid for the whole book, measured in lines.** A modular grid whose field heights are whole lines of body text.
   Code, prose, notes and pictures snap to it; hand-drawn pictures may break it on purpose. (Müller-Brockmann;
   Bringhurst's measured space.)

8. **Plain grounds and lots of room in the early chapters.** One ground colour, one shape, wide space. Density grows
   with the reader's confidence. (*Press Here*; Lionni; Maeda's restriction.)

9. **No numbers on the early canvas.** Chapter 1 shows no axes, grids or coordinates on the picture. The canvas frame
   is drawn by hand, like a sheet of paper. Coordinates arrive later as a tool, not a premise. (The maintainer's brief;
   the lesson of Maeda, taken in reverse.)

10. **The reader makes something on every spread.** Each spread ends with a task (change, guess, draw), and each
    chapter ends with a page for the reader's own work. (Munari; *Hello Ruby*'s activities; the course's Extend.)

11. **Story and practice on the same page.** No story at the front and exercises at the back; no in-jokes for
    programmers. (*Hello Ruby*, as a warning.)

12. **Warm edges, structured pages.** The structure is Swiss (grid, measured space); the surface is hand-made
    (imperfect lines, drawn frames, hand lettering for headings). The two together say "rigorous, and for you".
    (Müller-Brockmann and Lionni, held together.)

## Open questions for the page system

### Trim size

funground already knows A4, A5, B5, Letter, Square and others (`funground/pages.py`, in points), and can write a
print-ready PDF with bleed and crop marks (`f.save("book.pdf", bleed=f.mm(3), marks=True)`, `funground/export/printing.py`).
The options:

| Trim | For | Against |
|---|---|---|
| **Square, about 21 x 21 cm** | Picture-book feel; a square canvas sits naturally on a page; a spread is a 2:1 strip that holds a picture on one side and code on the other. | Code lines are short on a square page; not every print-on-demand service offers it cheaply *(check)*. |
| **Landscape, about 24 x 17 cm** | Code and picture side by side on one page; good on screen, since a PDF page fits a laptop. | Unusual on a bookshop shelf; a heavy spread when open (48 cm wide). |
| **Portrait, A4 or 21 x 27 cm (close to US 8.5 x 11 in)** | Cheapest and most available for print on demand; a workbook feel; room for code above a large picture. | Feels like a school workbook or manual, the opposite of our aim. |
| **Portrait, B5 or about 19 x 25 cm** | A friendly size for hands; picture large on one page, code and notes on the facing page. | Long code lines wrap; needs care at 9 to 10 pt code. |

My suggestion for the next step is to make one test spread (Chapter 1, first idea) at **square 21 cm** and at **B5**,
in PDF, and look at both on screen and printed. Planned from the start: 3 mm bleed, an inner margin that allows for
binding (at least 15 mm on a perfect-bound book of this size *(check with the printer)*), and pictures that run into the
bleed only on the picture side of the spread.

### A grid suggestion

A 6-column grid with 4 or 6 rows of fields, field heights in whole lines of the body text (for example 11 pt type on
15 pt lines). On a code spread: the picture takes the whole of one page (or 4 of its 6 columns, with the bleed);
the code takes 4 columns of the facing page and the side notes take the outer 2. Six columns also divide into three
equal Compare panels or two large ones. The grid should be a handful of numbers in the page system, so changing the
trim changes everything consistently.

### How code sits next to its picture

Three patterns to test, all with the picture larger than the code:

- **Facing pages.** Picture on the recto, code and notes on the verso. The calmest, and the best for print.
- **Picture above, code below** on one page. Best for a PDF read on screen, one page at a time.
- **Code wrapped by the picture.** For one-line sketches in Chapter 1 (a shape at the centre), the code can sit inside
  the picture's ground, in its corner, like a caption. This makes the point that one line is enough.

Code type: a monospaced face at about 9.5 to 10.5 pt, with funground's own colour for function names, not a grey box.
Notes in the margin at a smaller size, with a thin hand-drawn line to the code line they explain.

### Predict and Compare on a spread

One possible sequence across two turns, using the course's four steps (`docs/course/`):

- **Spread A.** Verso: the sketch, run, with its picture (the known). Recto: one changed line, highlighted, and
  **Predict**: "What will change?", with an empty hand-drawn frame for the reader's guess drawn in pencil.
- **Turn** (this is **Run**).
- **Spread B.** Verso: the real result, large. Recto: **Compare**, as small multiples: the original, the change, and
  two more values, same size, labelled with the one value that differs; then **Extend**: one task to try in Play.

In the PDF the turn is a page down, so the Predict page should end at the page edge with nothing of the answer
visible. Open question: does the PDF need a "single page" reading order that differs from print spreads, or can one
layout serve both?

### The hand-drawn manner

Two ways, and they can mix:

- **By hand.** Drawn on paper, scanned, cleaned, placed with `f.load_image()` and `f.image()`. The S-227 cut-out work
  (`spikes/14_cutout/`) is relevant to cleaning scans: removing the paper, tidying specks and holes. Best for
  headings, frames, arrows and spot drawings. Risk: the picture of the sketch's output must still be the real output,
  so scans decorate; they never replace a result.
- **By funground.** A hand-drawn line made from the sketch itself: each straight edge or curve redrawn as a path with
  small, smooth wobble from `f.noise()`, a slightly uneven stroke width, and a fixed seed so the page is the same every
  build. This keeps the result honest (it is still the sketch's own shape) and matches the book's message: the hand
  look is something you can program. Open question: is this a page-system effect applied to the book's pictures, or a
  public feature the reader learns (a story for later, and a semantic-contract decision for the maintainer)?

A middle way: frames, arrows and hand lettering drawn by hand once and reused; the sketch outputs printed clean but on
a paper-textured ground, with funground's hand line used only for diagrams the page system draws (margin arrows,
Compare frames).

### Other open questions

- How large is the book? Ten-spread chapters suggest about 20 to 24 pages per chapter.
- Colour on print: the PDF is RGB; print may need CMYK (see `spikes/11_cmyk/`). Bright screen colours (the reason our
  reader came) may dull in print; the palette for the book should be chosen to survive CMYK.
- Fonts: body, code and hand lettering need licences that allow embedding in a PDF and print.
- Does each spread link to Play (a short URL or a code) so the reader can run the sketch at once?

---

## Review (main session, 28 Oct)

**The pass criterion is met:** the study has ten books against the six required, each with what it teaches and what
funground takes or leaves. It was written by an Opus researcher subagent and reviewed here.

**What I checked:**
- **Every repository fact the study cites is true** on main at b88f261:
  - `f.save(..., bleed=, marks=)` in `funground/export/printing.py`;
  - the page sizes in `funground/pages.py` (`"Square"` is 600 pt, 21.2 cm);
  - `f.variations` in `funground/api.py`;
  - `docs/guide/projects/11_moving_the_paper.md`;
  - `spikes/11_cmyk/`.
- **I did not open the web sources.** The study already marks eight page descriptions as *unverified* (from memory of
  the books), and they stay so.
- **Two corrections:**
  - "The first book to teach artists to program" became "an early book", because the claim was not sourced.
  - A garbled phrase about Tufte's colour printing was fixed.

**Judgement:**
- **The study is sound and keeps to D-026:** it takes mechanisms (the turn as reveal, small multiples, a grid measured
  in lines), never looks.
- **Principles 1, 3 and 5 carry the most weight for the next steps:**
  - 1: the picture leads;
  - 3: the page turn is the Run button;
  - 5: the whole sketch made the picture beside it.
- **Principle 5 settles the production route in favour of funground as the layout engine.** The page system runs each
  sketch and places its output, so code and picture cannot disagree. The route is written down with the page system,
  not here.

**Choices for the next step,** decided by Claude within the spike, to be checked at review:
- **Trim:** build the test spread at both square 21 cm (`"Square"`) and B5, as the study suggests, and choose from the
  two PDFs.
- **Grid:** start with 6 columns, and field heights in whole lines of 11 on 15 pt body text.
- **Code beside its picture:** facing pages for print. The single-page reading order for the PDF is tested on the same
  spread, not assumed.
- **Hand-drawn manner:** the middle way.
  - The book's own diagrams get a funground hand line with a fixed seed.
  - Sketch outputs are printed clean.
  - Whether the hand line becomes a public feature is left to a later decision for the maintainer, not this spike.

**Still open for the maintainer:**
- The no-coordinates proposal for Chapter 1. It will be proposed as D-121, with the page system.
- The study's questions on CMYK colour, font licences and links to Play. They are answered in the page system.
