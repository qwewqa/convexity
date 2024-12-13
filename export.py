import multiprocessing as mp
from collections.abc import Callable
from pathlib import Path

from convexity.convert.sonolus_bandori import convert_sonolus_bandori_level_data
from convexity.convert.sonolus_llsif import convert_sonolus_llsif_level_data
from convexity.convert.sonolus_nanaon import convert_sonolus_nanaon_level_data
from convexity.convert.utils import convert_sonolus_level_item, get_level_items
from convexity.project import engine

BASE_DIR = Path("downloads")
PROCESS_COUNT = mp.cpu_count()


def convert_level(item: dict, base_url: str, converter: Callable, process_num: int):
    name = f"convexity-{item['name']}"
    level_dir = BASE_DIR / "levels" / name

    if (level_dir / "data").exists():
        print(f"[Process {process_num}] Skipped: {name}")
        return

    level_dir.mkdir(parents=True, exist_ok=True)
    converted = convert_sonolus_level_item(item, base_url, converter)
    converted.export("convexity").write_to_dir(level_dir)
    print(f"[Process {process_num}] Downloaded: {name}")


def download_levels(base_url: str, converter: Callable):
    print(f"Downloading level list from {base_url}...")
    items = get_level_items(base_url)

    print(f"Starting conversion using {PROCESS_COUNT} processes...")

    with mp.Pool(PROCESS_COUNT) as pool:
        pool.starmap(
            convert_level,
            [(item, base_url, converter, i) for i, item in enumerate(items)],
        )

    print("Done!")
    return items


def export_engine():
    engine.export().write_to_dir(BASE_DIR / "engines" / "convexity")


def main():
    download_levels(base_url="https://sonolus.milkbun.org/llsif/", converter=convert_sonolus_llsif_level_data)
    download_levels(base_url="https://sonolus.bestdori.com/official/", converter=convert_sonolus_bandori_level_data)
    download_levels(base_url="https://sonolus.milkbun.org/nanaon/", converter=convert_sonolus_nanaon_level_data)
    export_engine()


if __name__ == "__main__":
    main()
