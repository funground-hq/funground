"""The course's experiments in Play (S-216): examples/course/play.json must match the course it describes."""
import json
import re

from conftest import ROOT

COURSE = ROOT / "examples" / "course"
LESSONS = ROOT / "docs" / "course"
DATA = json.loads((COURSE / "play.json").read_text(encoding="utf-8"))


def headings(page: str) -> set[str]:
    text = (LESSONS / page).read_text(encoding="utf-8")
    return {m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", text, re.MULTILINE)}


def test_every_experiment_names_a_sketch_a_lesson_and_a_real_section():
    for experiment in DATA["experiments"]:
        assert (COURSE / experiment["sketch"]).is_file(), experiment["sketch"]
        lesson = DATA["lessons"][experiment["lesson"]]
        assert experiment["section"] in headings(lesson["page"]), (experiment["sketch"], experiment["section"])
        assert experiment["predict"].strip() and experiment["compare"].strip()


def test_every_experiment_is_linked_from_its_lesson():
    for experiment in DATA["experiments"]:
        if experiment.get("stage") == "extend":
            continue                                   # an Extend sketch is offered by Play, not by the lesson page
        page = (LESSONS / DATA["lessons"][experiment["lesson"]]["page"]).read_text(encoding="utf-8")
        assert f"examples/course/{experiment['sketch']}" in page, experiment["sketch"]


def test_each_lesson_page_exists_and_has_a_keep_note():
    for number, lesson in DATA["lessons"].items():
        assert (LESSONS / lesson["page"]).is_file(), lesson["page"]
        assert lesson["page"].startswith(f"{int(number):02d}_")
        assert "____" in lesson["keep"]


def extensions():
    return [e for e in DATA["experiments"] if e.get("stage") == "extend"]


def test_each_extend_entry_follows_the_experiment_it_extends():
    ordinary = {e["sketch"]: e for e in DATA["experiments"] if e.get("stage") != "extend"}
    assert {e["after"] for e in extensions()} == {"01_positions.py", "03_palettes.py", "05_rhythms.py"}
    for extension in extensions():
        base = ordinary[extension["after"]]                      # extends an ordinary experiment, not another Extend
        assert (extension["lesson"], extension["section"]) == (base["lesson"], base["section"])
        order = [e["sketch"] for e in DATA["experiments"]]
        same_lesson = [e["sketch"] for e in DATA["experiments"] if e["lesson"] == extension["lesson"]]
        assert same_lesson.index(extension["sketch"]) >= same_lesson.index(base["sketch"]), "Extend comes after its experiment"
        assert order.index(extension["sketch"]) == max(order.index(s) for s in same_lesson if s in order), "Extend closes its lesson"
        for field in ("title", "offer", "lead", "predict", "compare"):
            assert extension[field].strip(), (extension["sketch"], field)
    assert len({e["after"] for e in extensions()}) == len(extensions()), "one Extend for each experiment"


def test_the_extend_sketches_use_the_studio_vocabulary():
    for extension in extensions():
        code = (COURSE / extension["sketch"]).read_text(encoding="utf-8")
        assert "f.variations(" in code or "f.mark(" in code, extension["sketch"]
        assert code.startswith("# Original Funground course sketch. CC0; see ../LICENSE."), extension["sketch"]


def test_the_course_readme_lists_every_sketch_in_play_json():
    readme = (COURSE / "README.md").read_text(encoding="utf-8")
    for experiment in DATA["experiments"]:
        assert f"({experiment['sketch']})" in readme, experiment["sketch"]
