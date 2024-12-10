import itertools
import tempfile
import zipfile
from collections import deque
from io import BytesIO
from math import floor
from pathlib import Path
from typing import NamedTuple

from sonolus.script.level import Level, LevelData

from mania.play.bpm import BpmChange
from mania.play.init import Init
from mania.play.lane import Lane
from mania.play.note import Note, NoteVariant
from mania.play.stage import Stage
from mania.play.timescale import TimescaleChange, TimescaleGroup


class TimingPoint(NamedTuple):
    time: float
    beat_length: float
    meter: int
    sample_set: int
    sample_index: int
    volume: int
    uninherited: bool
    effects: int


class HitObject(NamedTuple):
    x: int
    y: int
    time: int
    type: int
    hit_sound: int
    object_params: list[str]
    hit_sample: list[float]

    @property
    def slide_end_time(self) -> float:
        return self.hit_sample[0]


def convert_osz(osz: bytes) -> list[Level]:
    levels = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(BytesIO(osz)) as zip_ref:
            zip_ref.extractall(temp_path)

            for osu_file in temp_path.glob("*.osu"):
                try:
                    with osu_file.open(encoding="utf-8") as f:
                        osu_data = f.read()
                    level = convert_osu(osu_data, temp_path)
                    if level is not None:
                        levels.append(level)

                except (OSError, UnicodeDecodeError) as e:
                    print(f"Error processing {osu_file.name}: {e}")
                    continue

    return levels


def convert_osu(data: str, assets: Path) -> Level | None:
    lines = deque(data.splitlines())
    parse_header(lines)
    sections = parse_sections(lines)

    general = parse_kv_section(sections["General"])
    metadata = parse_kv_section(sections["Metadata"])
    difficulty = parse_kv_section(sections["Difficulty"])

    audio_filename = general["AudioFilename"]
    mode = general["Mode"]
    if mode != "3":
        return None

    lane_count = int(difficulty["CircleSize"])

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

    def x_to_lane(x: float) -> float:
        return max(0, min(lane_count - 1, floor((x / 512) * lane_count))) - (lane_count - 1) / 2

    timing_points = parse_timing_points(sections["TimingPoints"])
    hit_objects = parse_hit_objects(sections["HitObjects"])

    bpm_changes = [
        BpmChange(beat=0, bpm=60, meter=0),
    ]
    bpm_changes_by_time = [(0, 60, 0)]
    timescale_group = TimescaleGroup()
    timescale_changes = [
        TimescaleChange(beat=0, scale=1),
    ]
    last_time = 0
    last_beat = 0
    last_bpm = 60
    for timing_point in timing_points:
        if timing_point.uninherited:
            bpm = 60000 / timing_point.beat_length
            section_beat = last_beat + (timing_point.time - last_time) / 60000 * last_bpm
            bpm_changes.append(BpmChange(beat=section_beat, bpm=bpm, meter=timing_point.meter))
            bpm_changes_by_time.append((timing_point.time, bpm, section_beat))
            last_time = timing_point.time
            last_beat = section_beat
            last_bpm = bpm
        else:
            section_beat = last_beat + (timing_point.time - last_time) / 60000 * last_bpm
            timescale_changes.append(
                TimescaleChange(
                    beat=section_beat,
                    scale=-100 / timing_point.beat_length,
                )
            )
    bpm_changes_by_time.append((1e8, 60, 0))

    notes = []
    bpm_change_index = 0
    for hit_object in hit_objects:
        while True:
            next_bpm_time, _, _ = bpm_changes_by_time[bpm_change_index + 1]
            if hit_object.time < next_bpm_time:
                break
            bpm_change_index += 1
        bpm_time, bpm, section_beat = bpm_changes_by_time[bpm_change_index]
        if hit_object.type & (1 << 0):
            notes.append(
                Note(
                    variant=NoteVariant.SINGLE,
                    beat=section_beat + (hit_object.time - bpm_time) / 60000 * bpm,
                    lane=x_to_lane(hit_object.x),
                    leniency=1,
                    timescale_group_ref=timescale_group.ref(),
                )
            )
        if hit_object.type & (1 << 7):
            start = Note(
                variant=NoteVariant.HOLD_START,
                beat=section_beat + (hit_object.time - bpm_time) / 60000 * bpm,
                lane=x_to_lane(hit_object.x),
                leniency=1,
                timescale_group_ref=timescale_group.ref(),
            )
            end = Note(
                variant=NoteVariant.HOLD_END,
                beat=section_beat + (hit_object.slide_end_time - bpm_time) / 60000 * bpm,
                lane=x_to_lane(hit_object.x),
                leniency=1,
                timescale_group_ref=timescale_group.ref(),
                prev_note_ref=start.ref(),
            )
            notes.append(start)
            notes.append(end)
        notes = sorted(notes, key=lambda note: note.beat)

    notes_by_beat: dict[float, list[Note]] = {}
    for note in notes:
        notes_by_beat.setdefault(note.beat, []).append(note)
    for group in notes_by_beat.values():
        group.sort(key=lambda note: note.lane)
        for a, b in itertools.pairwise(group):
            a.sim_note_ref @= b.ref()

    return Level(
        name=f"mania_v_{metadata["BeatmapSetID"]}_{metadata["BeatmapID"]}",
        title=f"{metadata["TitleUnicode"]} - {metadata["Version"]}",
        rating=0,
        artists=metadata["ArtistUnicode"],
        author=metadata["Creator"],
        bgm=(assets / audio_filename).read_bytes(),
        data=LevelData(
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
        ),
    )


def parse_header(lines: deque):
    if lines.popleft() != "osu file format v14":
        raise ValueError("Invalid osu file format")


def parse_sections(lines: deque) -> dict[str, list[str]]:
    sections = {}
    while lines:
        section_name, section_lines = parse_section(lines)
        sections[section_name] = section_lines
    return sections


def parse_section(lines: deque) -> tuple[str, list[str]]:
    advance_to_next_section(lines)
    section_name = lines.popleft()[1:-1]
    section_lines = []
    while lines and lines[0]:
        section_lines.append(lines.popleft())
    return section_name, section_lines


def parse_kv_section(lines: list[str]) -> dict[str, str]:
    section = {}
    for line in lines:
        key, value = line.split(":", 1)
        section[key.strip()] = value.strip()
    return section


def advance_to_next_section(lines: deque):
    while lines and not lines[0]:
        lines.popleft()


def parse_timing_points(lines: list[str]) -> list[TimingPoint]:
    results = []
    for line in lines:
        time, beat_length, meter, sample_set, sample_index, volume, uninherited, effects = line.split(",")
        results.append(
            TimingPoint(
                time=float(time),
                beat_length=float(beat_length),
                meter=int(meter),
                sample_set=int(sample_set),
                sample_index=int(sample_index),
                volume=int(volume),
                uninherited=uninherited == "1",
                effects=int(effects),
            )
        )
    return results


def parse_hit_objects(lines: list[str]) -> list[HitObject]:
    results = []
    for line in lines:
        x, y, time, object_type, hit_sound, *object_params, hit_sample = line.split(",")
        results.append(
            HitObject(
                x=int(x),
                y=int(y),
                time=int(time),
                type=int(object_type),
                hit_sound=int(hit_sound),
                object_params=object_params,
                hit_sample=[float(sample) for sample in hit_sample.split(":") if sample],
            )
        )
    return results
