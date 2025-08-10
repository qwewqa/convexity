from sonolus.script.runtime import level_score

from convexity.common.buckets import Buckets
from convexity.common.note import NoteVariant, note_window


def init_buckets():
    Buckets.tap_note.window @= note_window(NoteVariant.SINGLE) * 1000
    Buckets.hold_start_note.window @= note_window(NoteVariant.HOLD_START) * 1000
    Buckets.hold_end_note.window @= note_window(NoteVariant.HOLD_END) * 1000
    Buckets.hold_tick_note.window @= note_window(NoteVariant.HOLD_TICK) * 1000
    Buckets.flick_note.window @= note_window(NoteVariant.FLICK) * 1000
    Buckets.directional_flick_note.window @= note_window(NoteVariant.DIRECTIONAL_FLICK) * 1000
    Buckets.swing_note.window @= note_window(NoteVariant.SWING) * 1000


def init_score():
    level_score().update(
        perfect_multiplier=1,
        great_multiplier=0.5,
        good_multiplier=0.25,
    )


def init_life(note_archetype):
    note_archetype.life.update(
        perfect_increment=1,
        miss_increment=-100,
    )
