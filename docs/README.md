# funground documentation

This page collects all of funground's documentation, in the order you are likely to need it.
Each line says when to read the page.

## Start here

- [Getting started](guide/01_getting_started.md): read this first. It shows how to install funground
  and run your first sketch.
- The gallery browser: after you install, run `python -m funground.gallery` to browse every feature
  in a window, with its picture and its code.
  (Inside a virtual environment this is the same command. On Windows without activating it,
  use `.venv\Scripts\python -m funground.gallery`.)

## The guide

- [The guide](guide/README.md): read this to learn step by step. It has a learning path, and every
  chapter ends with things to try.

## Projects

- [Projects](guide/18_projects.md): read this when you know the basics and want to make something
  whole, such as a poster, a game or a raga explorer.

## The gallery

- [Examples Gallery](gallery/README.md): look here to see what a feature does, with a picture and a
  short sketch you can copy.
- [Showcase](gallery/SHOWCASE.md): look here for a dozen of the best pictures on one page.

## Reference

- [Quick Reference](reference/Quick_Reference.md): use it to find a function by topic, with a picture.
- [API reference](reference/API.md): use it to look up the exact arguments, results and an example for
  any name. It also lists the named colours, fixed words, page sizes, ragas and talas.
- [When something goes wrong](guide/errors.md): read it when you see an error message.
- [Glossary](guide/glossary.md): read it when a word is new to you.
- `help()` in Python: type `help(f.circle)` to read the same text as the API reference, without leaving
  your editor.

## Coming from other tools

- [funground compared with p5 and DrawBot](reference/Compared_with_p5_and_DrawBot.md): read this if you
  already know p5.js, Processing or DrawBot and want to find the matching names.
- [Coming from p5 and Processing](guide/14_coming_from_p5_processing.md): a guide chapter for p5.js and
  Processing users.
- [Coming from DrawBot](guide/15_coming_from_drawbot.md): a guide chapter for DrawBot users.

## For contributors

- [Developer documentation](developer/README.md): read this before you change the code. It covers the
  architecture, how to add a feature, testing and releasing.
- [Design documents](design/README.md): read these to learn why funground works the way it does.
  They hold the semantic contract, design notes and decisions.
- [How we work](PROCESS.md): read this to learn how sprints, stories and reviews run.
- [Quality notes](qa/Test_Strategy.md): read this for the test strategy and where each example
  came from ([example provenance](qa/Example_Provenance.md)).

## Project history

- [Roadmap](Roadmap.md): where the project is going.
- [Sprints](../sprints/): what was planned and done, one folder for each sprint.
- [Changelog](../CHANGELOG.md): what changed in each version.
