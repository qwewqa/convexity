from sonolus.script.archetype import archetype_life_of
from sonolus.script.runtime import level_life, level_score

from mania.common.buckets import Buckets
from mania.common.note import NoteVariant, note_window


def init_buckets():
    Buckets.tap_note.window @= note_window(NoteVariant.SINGLE) * 1000
    Buckets.hold_start_note.window @= note_window(NoteVariant.HOLD_START) * 1000
    Buckets.hold_end_note.window @= note_window(NoteVariant.HOLD_END) * 1000
    Buckets.hold_tick_note.window @= note_window(NoteVariant.HOLD_TICK) * 1000


def init_score():
    level_score().update(
        perfect_multiplier=1,
        great_multiplier=0.75,
        good_multiplier=0.5,
        consecutive_great_multiplier=0.01,
        consecutive_great_step=10,
        consecutive_great_cap=50,
    )


def init_life(note_archetype):
    level_life().update(
        consecutive_perfect_increment=50,
        consecutive_perfect_step=10,
    )

    archetype_life_of(note_archetype).update(
        perfect_increment=10,
        miss_increment=-100,
    )
