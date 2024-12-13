import itertools

from sonolus.script.level import LevelData

from convexity.common.note import NoteVariant
from convexity.convert.utils import convert_sonolus_level_item, get_sonolus_level_item, parse_entities
from convexity.play.bpm import BpmChange
from convexity.play.init import Init
from convexity.play.lane import Lane
from convexity.play.note import Note, UnscoredNote
from convexity.play.stage import Stage
from convexity.play.timescale import TimescaleChange, TimescaleGroup


def convert_sonolus_bandori_level(name: str, base_url: str = "https://sonolus.bestdori.com/official/") -> LevelData:
    item = get_sonolus_level_item(name, base_url)
    return convert_sonolus_level_item(item, base_url, convert_sonolus_bandori_level_data)


def convert_sonolus_bandori_level_data(data: dict) -> LevelData:
    bgm_offset = data["bgmOffset"]
    entities = parse_entities(data["entities"])

    lane_count = 7

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
                    variant=NoteVariant.SINGLE,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "FlickNote" | "SlideEndFlickNote":
                note = Note(
                    variant=NoteVariant.FLICK,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "DirectionalFlickNote":
                note = Note(
                    variant=NoteVariant.DIRECTIONAL_FLICK,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    direction=d["direction"] * d["size"],
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "SlideStartNote":
                note = Note(
                    variant=NoteVariant.HOLD_START,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "SlideEndNote":
                note = Note(
                    variant=NoteVariant.HOLD_END,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "SlideTickNote":
                note = Note(
                    variant=NoteVariant.HOLD_TICK,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "IgnoredNote":
                note = UnscoredNote(
                    variant=NoteVariant.HOLD_ANCHOR,
                    beat=d["#BEAT"],
                    lane=d["lane"],
                    timescale_group_ref=timescale_group.ref(),
                )
                notes.append(note)
                notes_by_index[i] = note
            case "CurvedSlideConnector" | "StraightSlideConnector" | "Stage" | "Initialization" | "SimLine":
                pass
            case _:
                raise ValueError(f"Unknown archetype: {archetype}")

    for archetype, d in entities:
        match archetype:
            case "CurvedSlideConnector" | "StraightSlideConnector":
                head = notes_by_index[d["head"]]
                tail = notes_by_index[d["tail"]]
                tail.prev_note_ref @= head.ref()

    notes.sort(key=lambda note: note.beat)
    for a, b in itertools.pairwise(notes):
        if a.beat != b.beat and abs(a.beat - b.beat) < 0.002:
            b.beat = a.beat
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
            Init(
                base_leniency=2.35,
            ),
            timescale_group,
            *timescale_changes,
            *stages,
            *lanes,
            *bpm_changes,
            *notes,
        ],
    )
