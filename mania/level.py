from sonolus.script.level import BpmChange, Level, LevelData

from mania.common.layout import LanePosition
from mania.play.init import Init
from mania.play.lane import Lane
from mania.play.note import Note, NoteVariant
from mania.play.stage import Stage
from mania.play.timescale_group import TimescaleChange, TimescaleGroup

level = Level(
    name="mania_level",
    title="Mania Level",
    bgm=None,
    data=LevelData(
        bgm_offset=0,
        entities=[
            BpmChange(beat=0, bpm=60),
            Init(),
            Stage(pos=LanePosition(-2, 2)),
            l1 := Lane(pos=LanePosition(-2, -1)),
            l2 := Lane(pos=LanePosition(-1, 0)),
            l3 := Lane(pos=LanePosition(0, 1)),
            l4 := Lane(pos=LanePosition(1, 2)),
            ts1 := TimescaleGroup(),
            TimescaleChange(beat=0, scale=1),
            TimescaleChange(beat=0.001, scale=999999),
            TimescaleChange(beat=0.002, scale=-0.1),
            *[
                [
                    head := Note(
                        variant=NoteVariant.HOLD_START,
                        beat=i,
                        lane_ref=l1.ref(),
                        timescale_group_ref=ts1.ref(),
                    ),
                    Note(
                        variant=NoteVariant.HOLD_END,
                        beat=i + 1 - 1 / 2,
                        lane_ref=l3.ref(),
                        timescale_group_ref=ts1.ref(),
                        prev_note_ref=head.ref(),
                    ),
                ]
                for i in range(2, 30)
            ],
            ts2 := TimescaleGroup(),
            TimescaleChange(beat=0, scale=1),
            TimescaleChange(beat=2, scale=1.5),
            *[
                [
                    head := Note(
                        variant=NoteVariant.HOLD_START,
                        beat=i,
                        lane_ref=l2.ref(),
                        timescale_group_ref=ts2.ref(),
                    ),
                    Note(
                        variant=NoteVariant.HOLD_END,
                        beat=i + 1 - 1 / 2,
                        lane_ref=l2.ref(),
                        timescale_group_ref=ts2.ref(),
                        prev_note_ref=head.ref(),
                    ),
                ]
                for i in range(2, 30)
            ],
            ts4 := TimescaleGroup(),
            TimescaleChange(beat=0, scale=1),
            *[
                tsc
                for i in range(1, 100)
                for tsc in [
                    TimescaleChange(beat=i / 4, scale=1),
                    TimescaleChange(beat=i / 4 + 1 / 8, scale=0),
                ]
            ],
            TimescaleChange(beat=100 / 4, scale=1),
            *[
                Note(beat=i / 4, lane_ref=l4.ref(), timescale_group_ref=ts4.ref())
                for i in range(8, 100)
            ],
        ],
    ),
)
