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
        page = (LESSONS / DATA["lessons"][experiment["lesson"]]["page"]).read_text(encoding="utf-8")
        assert f"examples/course/{experiment['sketch']}" in page, experiment["sketch"]


def test_each_lesson_page_exists_and_has_a_keep_note():
    for number, lesson in DATA["lessons"].items():
        assert (LESSONS / lesson["page"]).is_file(), lesson["page"]
        assert lesson["page"].startswith(f"{int(number):02d}_")
        assert "____" in lesson["keep"]
