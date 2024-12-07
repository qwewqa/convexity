from enum import IntEnum
from math import floor

from sonolus.script.bucket import Judgment, JudgmentWindow
from sonolus.script.interval import lerp, unlerp
from sonolus.script.particle import Particle, ParticleHandle
from sonolus.script.record import Record
from sonolus.script.sprite import Sprite
from sonolus.script.values import copy

from mania.common.buckets import Buckets, note_judgment_window
from mania.common.effect import SFX_DISTANCE, Effects
from mania.common.layout import (
    EPSILON,
    LanePosition,
    Layer,
    Layout,
    clamp_y_to_stage,
    connector_layout,
    lane_layout,
    note_layout,
    note_particle_layout,
    sim_line_layout,
)
from mania.common.options import Options
from mania.common.particle import Particles
from mania.common.skin import Skin


class NoteVariant(IntEnum):
    SINGLE = 0
    HOLD_START = 1
    HOLD_END = 2
    HOLD_TICK = 3


def note_window(variant: NoteVariant) -> JudgmentWindow:
    return note_judgment_window


def note_bucket(variant: NoteVariant):
    result = copy(Buckets.tap_note)
    match variant:
        case NoteVariant.SINGLE:
            result @= Buckets.tap_note
        case NoteVariant.HOLD_START:
            result @= Buckets.hold_start_note
        case NoteVariant.HOLD_END:
            result @= Buckets.hold_end_note
        case NoteVariant.HOLD_TICK:
            result @= Buckets.hold_tick_note
    return result


def note_body_sprite(variant: NoteVariant):
    result = copy(Skin.tap_note)
    match variant:
        case NoteVariant.SINGLE:
            result @= Skin.tap_note
        case NoteVariant.HOLD_START:
            result @= Skin.hold_start_note
        case NoteVariant.HOLD_END:
            result @= Skin.hold_end_note
        case NoteVariant.HOLD_TICK:
            result @= Skin.hold_tick_note
    return result


def note_head_sprite(variant: NoteVariant):
    return copy(Skin.hold_start_note)


def note_connector_sprite(variant: NoteVariant):
    return copy(Skin.connector)


def note_particle(variant: NoteVariant):
    result = copy(Particles.tap_note)
    match variant:
        case NoteVariant.SINGLE:
            result @= Particles.tap_note
        case NoteVariant.HOLD_START:
            result @= Particles.hold_note
        case NoteVariant.HOLD_END:
            result @= Particles.hold_note
        case NoteVariant.HOLD_TICK:
            result @= Particles.hold_note
    return result


def note_hold_particle(variant: NoteVariant):
    return copy(Particles.hold)


def draw_note_body(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return
    layout = note_layout(pos, y)
    sprite.draw(layout, z=Layer.NOTE + y + pos.mid / 100)


def draw_note_connector(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
    prev_pos: LanePosition,
    prev_y: float,
):
    if prev_y < Layout.min_safe_y and y < Layout.min_safe_y:
        return
    if prev_y > Layout.lane_length and y > Layout.lane_length:
        return

    if abs(prev_y - y) < EPSILON:
        y = prev_y - EPSILON

    clamped_prev_y = clamp_y_to_stage(prev_y)
    clamped_y = clamp_y_to_stage(y)
    clamped_prev_pos = lerp(
        prev_pos,
        pos,
        unlerp(prev_y, y, clamped_prev_y),
    ).scale_centered(Options.note_size)
    clamped_pos = lerp(
        prev_pos,
        pos,
        unlerp(prev_y, y, clamped_y),
    ).scale_centered(Options.note_size)

    arc_quality = 5
    n_segments = floor(abs(clamped_pos.mid - clamped_prev_pos.mid) * arc_quality * Options.arc) + 1
    for i in range(n_segments):
        segment_pos = lerp(clamped_prev_pos, clamped_pos, (i + 1) / n_segments)
        segment_y = lerp(clamped_prev_y, clamped_y, (i + 1) / n_segments)
        segment_prev_pos = lerp(clamped_prev_pos, clamped_pos, i / n_segments)
        segment_prev_y = lerp(clamped_prev_y, clamped_y, i / n_segments)
        layout = connector_layout(
            pos=segment_pos,
            y=segment_y,
            prev_pos=segment_prev_pos,
            prev_y=segment_prev_y,
        )
        sprite.draw(layout, z=Layer.CONNECTOR + max(y, prev_y) + pos.mid / 100, a=Options.connector_alpha)


def draw_note_sim_line(
    pos: LanePosition,
    y: float,
    sim_pos: LanePosition,
    sim_y: float,
):
    if not Options.sim_lines_enabled:
        return

    if y < Layout.min_safe_y and sim_y < Layout.min_safe_y:
        return
    if y > Layout.lane_length and sim_y > Layout.lane_length:
        return

    clamped_sim_y = clamp_y_to_stage(sim_y)
    clamped_y = clamp_y_to_stage(y)
    clamped_sim_pos = lerp(
        pos,
        sim_pos,
        unlerp(y, sim_y, clamped_sim_y) if abs(sim_y - y) > EPSILON else 1,
    ).scale_centered(Options.note_size)
    clamped_pos = lerp(
        pos,
        sim_pos,
        unlerp(y, sim_y, clamped_y) if abs(sim_y - y) > EPSILON else 0,
    ).scale_centered(Options.note_size)

    arc_quality = 5
    n_segments = floor(abs(clamped_pos.mid - clamped_sim_pos.mid) * arc_quality * Options.arc) + 1
    for i in range(n_segments):
        segment_pos = lerp(clamped_pos, clamped_sim_pos, (i + 1) / n_segments)
        segment_y = lerp(clamped_y, clamped_sim_y, (i + 1) / n_segments)
        segment_prev_pos = lerp(clamped_pos, clamped_sim_pos, i / n_segments)
        segment_prev_y = lerp(clamped_y, clamped_sim_y, i / n_segments)
        layout = sim_line_layout(
            pos=segment_pos,
            y=segment_y,
            sim_pos=segment_prev_pos,
            sim_y=segment_prev_y,
        )
        Skin.sim_line.draw(layout, z=Layer.CONNECTOR + max(y, sim_y) + pos.mid / 100, a=1)


def play_hit_effects(
    note_particle: Particle,
    pos: LanePosition,
    judgment: Judgment,
):
    play_hit_sfx(judgment)
    play_hit_particle(note_particle, pos)


def play_watch_hit_effects(
    note_particle: Particle,
    pos: LanePosition,
):
    play_hit_particle(note_particle, pos)


def schedule_watch_hit_effects(
    hit_time: float,
    judgment: Judgment,
):
    schedule_hit_sfx(judgment, hit_time)


def play_hit_sfx(judgment: Judgment):
    if not Options.sfx_enabled or Options.auto_sfx:
        return
    match judgment:
        case Judgment.PERFECT:
            Effects.perfect.play(SFX_DISTANCE)
        case Judgment.GREAT:
            Effects.great.play(SFX_DISTANCE)
        case Judgment.GOOD:
            Effects.good.play(SFX_DISTANCE)
        case _:
            pass


def schedule_auto_hit_sfx(judgment: Judgment, target_time: float):
    if not Options.auto_sfx:
        return
    schedule_hit_sfx(judgment, target_time)


def schedule_hit_sfx(judgment: Judgment, target_time: float):
    if not Options.sfx_enabled:
        return
    match judgment:
        case Judgment.PERFECT:
            Effects.perfect.schedule(target_time, SFX_DISTANCE)
        case Judgment.GREAT:
            Effects.great.schedule(target_time, SFX_DISTANCE)
        case Judgment.GOOD:
            Effects.good.schedule(target_time, SFX_DISTANCE)
        case _:
            pass


def play_hit_particle(
    note_particle: Particle,
    pos: LanePosition,
):
    if Options.note_effect_enabled:
        note_particle.spawn(
            note_particle_layout(pos),
            duration=0.5,
        )
    if Options.lane_effect_enabled:
        Particles.lane.spawn(
            lane_layout(pos),
            duration=0.2,
        )


class HoldHandle(Record):
    handle: ParticleHandle

    def update(self, particle: Particle, pos: LanePosition):
        if not Options.note_effect_enabled:
            return
        if self.handle.id == 0:
            self.handle @= particle.spawn(
                note_particle_layout(pos),
                duration=1.0,
                loop=True,
            )
        else:
            self.handle.move(note_particle_layout(pos))

    def destroy(self):
        if self.handle.id != 0:
            self.handle.destroy()
            self.handle.id = 0
