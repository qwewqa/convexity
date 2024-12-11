import gzip
import json
from functools import lru_cache
from typing import NamedTuple
from urllib.request import Request, urlopen


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
