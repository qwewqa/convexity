from enum import IntEnum
from math import floor

from sonolus.script.bucket import Judgment, JudgmentWindow
from sonolus.script.easing import ease_out_quad
from sonolus.script.interval import lerp, unlerp
from sonolus.script.particle import Particle, ParticleHandle
from sonolus.script.quad import Quad
from sonolus.script.record import Record
from sonolus.script.runtime import time
from sonolus.script.sprite import Sprite
from sonolus.script.values import copy, zeros
from sonolus.script.vec import Vec2

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
    transform_vec,
)
from mania.common.options import Options
from mania.common.particle import Particles
from mania.common.skin import Skin


class NoteVariant(IntEnum):
    SINGLE = 0
    HOLD_START = 1
    HOLD_END = 2
    HOLD_TICK = 3
    HOLD_ANCHOR = 4
    FLICK = 5
    DIRECTIONAL_FLICK = 6


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
        case NoteVariant.FLICK:
            result @= Buckets.flick_note
        case NoteVariant.DIRECTIONAL_FLICK:
            result @= Buckets.directional_flick_note
    return result


def note_body_sprite(variant: NoteVariant, direction: int):
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
        case NoteVariant.FLICK:
            result @= Skin.flick_note
        case NoteVariant.DIRECTIONAL_FLICK:
            if direction > 0:
                result @= Skin.right_flick_note
            else:
                result @= Skin.left_flick_note
    return result


def note_arrow_sprite(variant: NoteVariant, direction: int):
    result = copy(Skin.flick_arrow)
    match variant:
        case NoteVariant.FLICK:
            result @= Skin.flick_arrow
        case NoteVariant.DIRECTIONAL_FLICK:
            if direction > 0:
                result @= Skin.right_flick_arrow
            else:
                result @= Skin.left_flick_arrow
    return result


def note_head_sprite(variant: NoteVariant):
    return copy(Skin.hold_start_note)


def note_connector_sprite(variant: NoteVariant):
    return copy(Skin.connector)


def note_particle(variant: NoteVariant, direction: int):
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
        case NoteVariant.FLICK:
            result @= Particles.flick_note
        case NoteVariant.DIRECTIONAL_FLICK:
            if direction > 0:
                result @= Particles.right_flick_note
            else:
                result @= Particles.left_flick_note
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
        sprite.draw(layout, z=Layer.CONNECTOR - y + pos.mid / 100, a=Options.connector_alpha)


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
        Skin.sim_line.draw(layout, z=Layer.CONNECTOR - y + pos.mid / 100, a=1)


def draw_note_arrow(
    sprite: Sprite,
    direction: int,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return

    period = 0.3
    count = max(abs(direction), 1)
    start_lane = pos.mid
    end_lane = start_lane + direction
    offset = ((time() + 5) % period) / period
    fade_progress = 1 / 4 / count
    for i in range(count):
        progress = ((i + offset) % count) / count
        if progress < fade_progress:
            alpha = ease_out_quad(progress / fade_progress)
        elif progress > 1 - fade_progress:
            alpha = ease_out_quad((1 - progress) / fade_progress)
        else:
            alpha = 1
        lane = lerp(start_lane, end_lane, progress)
        layout = zeros(Quad)
        if direction == 0:
            y_offset = lerp(0.0, 0.5, progress)
            base_bl = transform_vec(Vec2(lane - 0.5, y))
            base_br = transform_vec(Vec2(lane + 0.5, y))
            ort = (base_br - base_bl).orthogonal()
            bl = base_bl + ort * y_offset
            br = base_br + ort * y_offset
            tl = bl + ort
            tr = br + ort
            layout @= Quad(
                bl=bl,
                br=br,
                tl=tl,
                tr=tr,
            )
        else:
            up_layout = note_layout(LanePosition(lane - 0.5, lane + 0.5), y)
            if direction > 0:
                layout @= Quad(
                    bl=up_layout.tl,
                    br=up_layout.bl,
                    tl=up_layout.tr,
                    tr=up_layout.br,
                )
            else:
                layout @= Quad(
                    bl=up_layout.br,
                    br=up_layout.tr,
                    tl=up_layout.bl,
                    tr=up_layout.tl,
                )
        sprite.draw(layout, z=Layer.ARROW - y + lane / 100, a=alpha)


def flick_velocity_threshold(direction: int = 0):
    return max(8.0, 4.0 * abs(direction)) * Layout.reference_length


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
