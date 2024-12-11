import itertools
from urllib.parse import urljoin

from sonolus.script.level import Level, LevelData

from mania.common.note import NoteVariant
from mania.convert.utils import get_bytes, get_json, get_json_gzip, make_relative, parse_entities
from mania.play.bpm import BpmChange
from mania.play.init import Init
from mania.play.lane import Lane
from mania.play.note import Note
from mania.play.stage import Stage
from mania.play.timescale import TimescaleChange, TimescaleGroup


def convert_sonolus_llsif_level(name: str, base_url: str = "https://sonolus.milkbun.org/llsif/") -> Level:
    item = get_json(urljoin(urljoin(base_url, "sonolus/levels/"), name + "?localization=en"))["item"]
    name = item["name"]
    rating = item["rating"]
    title = item["title"]
    artists = item["artists"]
    author = item["author"]
    cover = get_bytes(urljoin(base_url, item["cover"]["url"]))
    bgm = get_bytes(urljoin(base_url, item["bgm"]["url"]))
    raw_data = get_json_gzip(urljoin(base_url, make_relative(item["data"]["url"])))
    level_data = convert_sonolus_llsif_level_data(raw_data)
    return Level(
        name=f"mania-v-{name}",
        title=title,
        rating=rating,
        artists=artists,
        author=author,
        cover=cover,
        bgm=bgm,
        data=level_data,
    )


def convert_sonolus_llsif_level_data(data: dict) -> LevelData:
    bgm_offset = data["bgmOffset"]
    entities = parse_entities(data["entities"])

    lane_count = 9
    leniency = 1

    stages = [
        Stage(
            lane=0,
            width=lane_count,
        )
    ]
    lanes = [
        Lane(
            lane=i - (lane_count - 1) / 2,
        )
        for i in range(lane_count)
    ]
    notes = []
    notes_by_index = {}
    bpm_changes = []
    timescale_group = TimescaleGroup()
    timescale_changes = [
        TimescaleChange(
            beat=0,
            scale=1,
        )
    ]
    for i, (archetype, d) in enumerate(entities):
        match archetype:
            case "#BPM_CHANGE":
                bpm_changes.append(
                    BpmChange(
                        beat=d["#BEAT"],
                        bpm=d["#BPM"],
                        meter=4,
                    )
                )
            case "TapNote":
                note = Note(
                    variant=NoteVariant.SINGLE if not d.get("hold") else NoteVariant.HOLD_START,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    leniency=leniency,
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "HoldNote":
                prev = notes_by_index[int(d["prev"])]
                note = Note(
                    variant=NoteVariant.HOLD_END,
                    beat=d["#BEAT"],
                    lane=prev.lane,
                    leniency=leniency,
                    timescale_group_ref=timescale_group.ref(),
                    prev_note_ref=prev.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "SwingNote":
                note = Note(
                    variant=NoteVariant.SWING,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    leniency=leniency,
                    timescale_group_ref=timescale_group.ref(),
                    direction=d["direction"],
                )
                notes.append(note)
                notes_by_index[i] = note
            case "TimescaleChange":
                timescale_changes.append(
                    TimescaleChange(
                        beat=d["#BEAT"],
                        scale=d["#TIMESCALE"],
                    )
                )

    notes_by_beat: dict[float, list[Note]] = {}
    for note in notes:
        notes_by_beat.setdefault(note.beat, []).append(note)
    for group in notes_by_beat.values():
        group.sort(key=lambda note: note.lane)
        for a, b in itertools.pairwise(n for n in group if n.variant != NoteVariant.HOLD_ANCHOR):
            a.sim_note_ref @= b.ref()

    return LevelData(
        bgm_offset=bgm_offset,
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
