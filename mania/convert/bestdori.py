import itertools
import json
from urllib.request import Request, urlopen

from sonolus.script.level import Level, LevelData

from mania.common.note import NoteVariant
from mania.play.bpm import BpmChange
from mania.play.init import Init
from mania.play.lane import Lane
from mania.play.note import Note, UnscoredNote
from mania.play.stage import Stage
from mania.play.timescale import TimescaleChange, TimescaleGroup


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


difficulty_names = {
    "0": "easy",
    "1": "normal",
    "2": "hard",
    "3": "expert",
    "4": "special",
}


def get_bestdori_official(chart_id: int):
    song_data = get_json(f"https://bestdori.com/api/songs/{chart_id}.json")
    bgm = get_bytes(f"https://bestdori.com/assets/jp/sound/bgm{chart_id}_rip/bgm{chart_id}.mp3")
    title = song_data["musicTitle"][1] or song_data["musicTitle"][0]
    artist = song_data["composer"][1] or song_data["composer"][0]
    for difficulty_id in ("3", "4"):
        if difficulty_id not in song_data["difficulty"]:
            continue
        difficulty_data = song_data["difficulty"][difficulty_id]
        difficulty_level = difficulty_data["playLevel"]
        chart_data = get_json(f"https://bestdori.com/api/charts/{chart_id}/{difficulty_names[difficulty_id]}.json")
        level_data = convert_bestdori(chart_data)
        yield Level(
            name=f"mania_v_bestdori_{chart_id}_{difficulty_id}",
            title=f"{title} [{difficulty_names[difficulty_id]}]",
            rating=difficulty_level,
            artists=artist,
            author="Bandori",
            bgm=bgm,
            data=level_data,
        )


def convert_bestdori(data: list[dict]) -> LevelData:
    lane_count = 7

    def convert_lane(x: float) -> float:
        return x - 3

    stages = [
        Stage(
            lane=0,
            width=lane_count,
        )
    ]
    lanes = [
        Lane(
            lane=convert_lane(i),
        )
        for i in range(lane_count)
    ]
    notes = []
    bpm_changes = []
    timescale_group = TimescaleGroup()
    timescale_changes = [
        TimescaleChange(beat=0, scale=1),
    ]
    for entry in data:
        match entry["type"]:
            case "BPM":
                bpm_changes.append(
                    BpmChange(
                        bpm=entry["bpm"],
                        beat=entry["beat"],
                    )
                )
            case "Single":
                notes.append(
                    Note(
                        variant=NoteVariant.SINGLE if not entry.get("flick", False) else NoteVariant.FLICK,
                        beat=entry["beat"],
                        lane=convert_lane(entry["lane"]),
                        leniency=2,
                        timescale_group_ref=timescale_group.ref(),
                    )
                )
            case "Slide" | "Long":
                connections = entry["connections"]
                prev_note = Note(
                    variant=NoteVariant.HOLD_START,
                    beat=connections[0]["beat"],
                    lane=convert_lane(connections[0]["lane"]),
                    leniency=2,
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(prev_note)
                for i, connection in enumerate(connections[1:], 1):
                    if i == len(connections) - 1:
                        variant = NoteVariant.HOLD_END
                    elif connection.get("hidden", False):
                        variant = NoteVariant.HOLD_ANCHOR
                    elif connection.get("flick", False):
                        variant = NoteVariant.FLICK
                    else:
                        variant = NoteVariant.HOLD_TICK
                    note = (Note if not connection.get("hidden", False) else UnscoredNote)(
                        variant=variant,
                        beat=connection["beat"],
                        lane=convert_lane(connection["lane"]),
                        leniency=2,
                        timescale_group_ref=timescale_group.ref(),
                        prev_note_ref=prev_note.ref(),
                    )
                    notes.append(note)
                    prev_note = note
            case "Directional":
                notes.append(
                    Note(
                        variant=NoteVariant.DIRECTIONAL_FLICK,
                        beat=entry["beat"],
                        lane=convert_lane(entry["lane"]),
                        direction=entry["width"] * (1 if entry["direction"] == "Right" else -1),
                        leniency=2,
                        timescale_group_ref=timescale_group.ref(),
                    )
                )

    notes_by_beat: dict[float, list[Note]] = {}
    for note in notes:
        notes_by_beat.setdefault(note.beat, []).append(note)
    for group in notes_by_beat.values():
        group.sort(key=lambda note: note.lane)
        for a, b in itertools.pairwise(n for n in group if n.variant != NoteVariant.HOLD_ANCHOR):
            a.sim_note_ref @= b.ref()

    notes.sort(key=lambda note: note.beat)

    return LevelData(
        bgm_offset=0,
        entities=[
            Init(),
            timescale_group,
            *timescale_changes,
            *stages,
            *lanes,
            *bpm_changes,
            *notes,
        ],
    )
