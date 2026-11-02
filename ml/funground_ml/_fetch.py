"""Getting a model file: the copy in ``models/`` beside the sketch, or one download (D-125; the same idea as web fonts, D-119).

funground's own HTTPS request (``urllib``, no Hub library). The file is written under a temporary name, checked against
its size and SHA-256, and only then renamed, so a half download or a changed file is never kept. A second run finds the
copy and never asks the network. ``FUNGROUND_ML_MODELS`` names another folder (for tests and CI).
"""
from __future__ import annotations

import hashlib
import os
import socket
from http.client import HTTPException
from importlib import metadata
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ._models import MODELS, TASKS, Model

FOLDER_NAME = "models"
ENVIRONMENT = "FUNGROUND_ML_MODELS"
TIMEOUT = 30.0              # seconds to wait for the site, each time it is asked for more
CHUNK = 1 << 20

_open = urlopen             # tests put a local opener here: no unit test uses the network
_checked: set[tuple[str, str]] = set()      # (folder, file) pairs whose checksum was verified in this process


def _version() -> str:
    try:
        return metadata.version("funground-ml")
    except metadata.PackageNotFoundError:
        return "dev"


def models_folder(base_dir: str | None) -> str:
    """The folder that holds the copies: ``$FUNGROUND_ML_MODELS``, else ``models/`` beside the sketch (the current folder
    when there is no sketch file)."""
    named = os.environ.get(ENVIRONMENT)
    if named:
        return os.path.abspath(named)
    return os.path.join(base_dir if base_dir is not None else os.getcwd(), FOLDER_NAME)


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _is_good(path: str, model: Model) -> bool:
    return os.path.getsize(path) == model.size and sha256_of(path) == model.sha256


def _megabytes(size: int) -> int:
    return max(1, round(size / 1_000_000))


def _short(reason: object) -> str:
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "timed out"
    return (str(reason).strip() or type(reason).__name__)[:80]


def _words(model: Model) -> str:
    return model.name.replace("_", " ")


def _offline(who: str, model: Model, reason: str, folder_word: str) -> str:
    return (f"{who}: could not download the {_words(model)} from huggingface.co ({reason}). "
            f"Run the sketch once while online; after that funground uses the copy in {folder_word}/.")


def _download(model: Model, target: str, who: str, folder_word: str) -> None:
    """Fetch *model* into *target*, checked, or raise. Nothing is left under a temporary name."""
    temporary = target + ".part"
    digest, received = hashlib.sha256(), 0
    request = Request(model.url, headers={"User-Agent": f"funground-ml/{_version()}"})
    try:
        with _open(request, timeout=TIMEOUT) as response, open(temporary, "wb") as out:
            while chunk := response.read(CHUNK):
                received += len(chunk)
                if received > model.size:           # more than the table says: stop at once
                    break
                digest.update(chunk)
                out.write(chunk)
        if received != model.size or digest.hexdigest() != model.sha256:
            raise ValueError(f"{who}: the file downloaded for the {_words(model)} is not the one funground expects "
                             "(its checksum is different), so it was not kept. Try again. If it keeps happening, "
                             "tell the funground team.")
        os.replace(temporary, target)
    except HTTPError as error:
        raise ConnectionError(f"{who}: could not download '{model.url}' (the site answered {error.code}).") from None
    except URLError as error:
        raise ConnectionError(_offline(who, model, _short(error.reason), folder_word)) from None
    except (OSError, HTTPException) as error:       # a timeout while reading, a dropped line, a full disk
        raise ConnectionError(_offline(who, model, _short(error), folder_word)) from None
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def ensure(task: str, base_dir: str | None, who: str) -> dict[str, str]:
    """The paths of the files for *task* ("pose", "hand" or "person"), downloading the ones that are missing or wrong.

    Returns:
        {"detector": path, "landmarks": path} for pose and hand, {"model": path} for person. A call that has to download
        prints one line first.
    """
    folder = models_folder(base_dir)
    folder_word = FOLDER_NAME if not os.environ.get(ENVIRONMENT) else folder
    paths: dict[str, str] = {}
    missing: list[Model] = []
    names = TASKS[task]
    for role, name in zip(("model",) if len(names) == 1 else ("detector", "landmarks"), names):
        model = MODELS[name]
        paths[role] = os.path.join(folder, model.local_name)
        if (folder, model.local_name) in _checked and os.path.exists(paths[role]):
            continue
        if os.path.exists(paths[role]) and _is_good(paths[role], model):
            _checked.add((folder, model.local_name))
        else:
            missing.append(model)
    if missing:
        total = sum(m.size for m in missing)
        print(f"Downloading the {task} model, {_megabytes(total)} MB, once. "
              f"After that funground uses the copy in {folder_word}/.")
        os.makedirs(folder, exist_ok=True)
        for model in missing:
            _download(model, os.path.join(folder, model.local_name), who, folder_word)
            _checked.add((folder, model.local_name))
    return paths
