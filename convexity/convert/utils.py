import gzip
import json
from collections.abc import Callable
from functools import lru_cache
from os import PathLike
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from sonolus.script.level import Level, LevelData
from sonolus.script.metadata import Tag


@lru_cache
def get_bytes(url: str) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    request = Request(url, headers=headers)
    with urlopen(request) as response:
        return response.read()


def get_str(url: str) -> str:
    return get_bytes(url).decode("utf-8")


def get_json(url: str) -> dict | list:
    return json.loads(get_str(url))


def get_json_gzip(url: str) -> dict | list:
    data = get_bytes(url)
    return json.loads(gzip.decompress(data).decode("utf-8"))


def make_relative(path: str) -> str:
    if path and path[0] == "/":
        return path[1:]
    return path


class EntityData(NamedTuple):
    archetype: str
    data: dict[str, float]


def parse_entities(data: list[dict]) -> list[EntityData]:
    indexes_by_name = {e["name"]: i for i, e in enumerate(data) if "name" in e}
    return [
        EntityData(
            archetype=e["archetype"],
            data={d["name"]: d["value"] if "value" in d else indexes_by_name.get(d["ref"], 0) for d in e["data"]},
        )
        for e in data
    ]


def get_sonolus_level_item(name: str, base_url: str) -> dict:
    return get_json(urljoin(urljoin(base_url, "sonolus/levels/"), name + "?localization=en"))["item"]


def get_level_items(base_url: str) -> list[dict]:
    levels_url = urljoin(base_url, "sonolus/levels/list?localization=en")
    page = 0
    results = []
    while True:
        data = get_json(levels_url + f"&page={page}")
        results.extend(data["items"])
        page += 1
        if page >= data["pageCount"]:
            break
    return results


def get_playlist_items(base_url: str) -> list[dict]:
    playlist_url = urljoin(base_url, "sonolus/playlists/list?localization=en")
    page = 0
    results = []
    while True:
        data = get_json(playlist_url + f"&page={page}")
        results.extend(data["items"])
        page += 1
        if page >= data["pageCount"]:
            break
    return results


def write_playlist_items(path: PathLike, tag: str | None, items: list[dict]):
    for item in items:
        pl_path = Path(path) / f"convexity-{item["name"]}"
        pl_path.mkdir(parents=True, exist_ok=True)
        item = {
            "version": item["version"],
            "title": {"en": item["title"]},
            "subtitle": {"en": item["subtitle"]},
            "author": {"en": item["author"]},
            "levels": [f"convexity-{level_item["name"]}" for level_item in item["levels"]],
            "tags": [Tag(title=tag["title"], icon=tag.get("icon")).as_dict() for tag in item["tags"]],
        }
        if tag:
            item["tags"].append(Tag(title=tag).as_dict())
        (pl_path / "item.json").write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")


def convert_sonolus_level_item(item: dict, base_url: str, tag: str | None, data_converter: Callable[[dict], LevelData]):
    tags = [Tag(title=tag["title"], icon=tag.get("icon")) for tag in item["tags"]]
    if tag:
        tags.append(Tag(title=tag))
    return Level(
        name=f"convexity-{item["name"]}",
        rating=item["rating"],
        title=item["title"],
        artists=item["artists"],
        author=item["author"],
        description=item.get("description"),
        tags=tags,
        cover=get_bytes(urljoin(base_url, item["cover"]["url"].replace(" ", "%20"))),
        bgm=get_bytes(urljoin(base_url, item["bgm"]["url"].replace(" ", "%20"))),
        preview=get_bytes(urljoin(base_url, item["preview"]["url"].replace(" ", "%20")))
        if item.get("preview")
        else None,
        data=data_converter(get_json_gzip(urljoin(base_url, make_relative(item["data"]["url"].replace(" ", "%20"))))),
    )
