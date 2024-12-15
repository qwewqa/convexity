from __future__ import annotations

from enum import IntEnum
from math import floor, pi

from sonolus.script.bucket import Judgment, JudgmentWindow
from sonolus.script.easing import ease_out_cubic, ease_out_quad
from sonolus.script.effect import Effect
from sonolus.script.interval import lerp, remap, unlerp
from sonolus.script.particle import Particle, ParticleHandle
from sonolus.script.quad import Quad
from sonolus.script.record import Record
from sonolus.script.runtime import time
from sonolus.script.sprite import Sprite
from sonolus.script.values import copy, zeros
from sonolus.script.vec import Vec2

from convexity.common.buckets import Buckets, note_judgment_window, tick_judgment_window
from convexity.common.effect import SFX_DISTANCE, Effects
from convexity.common.layout import (
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
from convexity.common.options import Options
from convexity.common.particle import Particles
from convexity.common.skin import Skin


class NoteVariant(IntEnum):
    SINGLE = 0
    HOLD_START = 1
    HOLD_END = 2
    HOLD_TICK = 3
    HOLD_ANCHOR = 4
    FLICK = 5
    DIRECTIONAL_FLICK = 6
    SWING = 7


def note_window(variant: NoteVariant) -> JudgmentWindow:
    result = copy(note_judgment_window)
    match variant:
        case (
            NoteVariant.SINGLE
            | NoteVariant.HOLD_START
            | NoteVariant.HOLD_END
            | NoteVariant.FLICK
            | NoteVariant.DIRECTIONAL_FLICK
        ):
            result @= note_judgment_window
        case NoteVariant.HOLD_TICK | NoteVariant.HOLD_ANCHOR | NoteVariant.SWING:
            result @= tick_judgment_window
    result *= Options.window_size
    return result


def note_bucket(variant: NoteVariant):
    result = copy(Buckets.tap_note)
    match variant:
        case NoteVariant.SINGLE:
            result @= Buckets.tap_note
        case NoteVariant.HOLD_START:
            result @= Buckets.hold_start_note
        case NoteVariant.HOLD_END:
            result @= Buckets.hold_end_note
        case NoteVariant.HOLD_TICK | NoteVariant.HOLD_ANCHOR:
            result @= Buckets.hold_tick_note
        case NoteVariant.FLICK:
            result @= Buckets.flick_note
        case NoteVariant.DIRECTIONAL_FLICK:
            result @= Buckets.directional_flick_note
        case NoteVariant.SWING:
            result @= Buckets.swing_note
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
        case NoteVariant.SWING:
            result @= Skin.swing_note
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
        case NoteVariant.SWING:
            result @= Skin.swing_arrow
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
        case NoteVariant.SWING:
            result @= Particles.swing_note
    return result


def note_hold_particle(variant: NoteVariant):
    return copy(Particles.hold)


def y_to_alpha(y: float):
    progress = unlerp(
        Layout.lane_length,
        0,
        y,
    )
    if Options.extend_lanes and 0.0 <= progress <= 0.2:
        return ease_out_cubic(remap(0.0, 0.2, 0, 1, progress))
    if Options.hidden != 0 and progress > 1 - Options.hidden - 0.1:
        return ease_out_cubic(remap(1 - Options.hidden - 0.1, 1 - Options.hidden + 0.1, 1, 0, progress))
    return 1


def draw_note_body(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return
    layout = note_layout(pos, y)
    sprite.draw(layout, z=Layer.NOTE + y + pos.mid / 100, a=y_to_alpha(y))


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

    arc_quality = Options.arc_quality
    n_segments = (
        floor(abs(clamped_pos.mid - clamped_prev_pos.mid) * arc_quality * Options.arc)
        + floor(abs(clamped_y - clamped_prev_y) * arc_quality)
        + 1
    )
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
        sprite.draw(
            layout,
            z=Layer.CONNECTOR - y + pos.mid / 100,
            a=Options.connector_alpha * y_to_alpha((segment_y + segment_prev_y) / 2),
        )


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

    arc_quality = Options.arc_quality
    n_segments = (
        floor(abs(clamped_pos.mid - clamped_sim_pos.mid) * arc_quality * Options.arc)
        + floor(abs(clamped_y - clamped_sim_y) * arc_quality)
        + 1
    )
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
        Skin.sim_line.draw(
            layout, z=Layer.CONNECTOR - y + pos.mid / 100, a=y_to_alpha((segment_y + segment_prev_y) / 2)
        )


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
    lane_offset = 0
    if direction > 0:
        lane_offset = 0.4
    elif direction < 0:
        lane_offset = -0.4
    start_lane = pos.mid + lane_offset
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
        sprite.draw(layout, z=Layer.ARROW - y + lane / 100, a=alpha * y_to_alpha(y))


def draw_swing_arrow(
    sprite: Sprite,
    direction: int,
    pos: LanePosition,
    y: float,
):
    y_offset = 0
    lane = pos.mid
    base_bl = transform_vec(Vec2(lane - 0.5, y))
    base_br = transform_vec(Vec2(lane + 0.5, y))
    ort = (base_br - base_bl).orthogonal()
    bl = base_bl + ort * y_offset
    br = base_br + ort * y_offset
    tl = bl + ort
    tr = br + ort
    layout = Quad(
        bl=bl,
        br=br,
        tl=tl,
        tr=tr,
    )
    if direction > 0:
        layout @= layout.rotate_centered(-pi / 2)
    elif direction < 0:
        layout @= layout.rotate_centered(pi / 2)
    sprite.draw(layout, z=Layer.ARROW - y + lane / 100, a=y_to_alpha(y))


def flick_velocity_threshold(direction: int = 0):
    if direction == 0:
        return 6.0 * Layout.reference_length
    else:
        return 3.0 * abs(direction) * Layout.reference_length


def swing_velocity_threshold():
    return 3.0 * Layout.reference_length


def note_hit_sfx(variant: NoteVariant, judgment: Judgment):
    result = zeros(Effect)
    match variant:
        case NoteVariant.FLICK | NoteVariant.DIRECTIONAL_FLICK:
            match judgment:
                case Judgment.PERFECT:
                    result @= Effects.perfect_alt
                case Judgment.GREAT:
                    result @= Effects.great_alt
                case Judgment.GOOD:
                    result @= Effects.good_alt
        case _:
            match judgment:
                case Judgment.PERFECT:
                    result @= Effects.perfect
                case Judgment.GREAT:
                    result @= Effects.great
                case Judgment.GOOD:
                    result @= Effects.good
    return result


def play_hit_effects(
    variant: NoteVariant,
    note_particle: Particle,
    pos: LanePosition,
    judgment: Judgment,
):
    play_hit_sfx(variant, judgment)
    play_hit_particle(note_particle, pos)


def play_watch_hit_effects(
    note_particle: Particle,
    pos: LanePosition,
):
    play_hit_particle(note_particle, pos)


def schedule_watch_hit_effects(
    variant: NoteVariant,
    hit_time: float,
    judgment: Judgment,
):
    schedule_hit_sfx(variant, judgment, hit_time)


def play_hit_sfx(variant: NoteVariant, judgment: Judgment):
    if not Options.sfx_enabled or Options.auto_sfx:
        return
    effect = note_hit_sfx(variant, judgment)
    if effect.id == 0:
        return
    effect.play(SFX_DISTANCE)


def schedule_auto_hit_sfx(variant: NoteVariant, judgment: Judgment, target_time: float):
    if not Options.auto_sfx:
        return
    schedule_hit_sfx(variant, judgment, target_time)


def schedule_hit_sfx(variant: NoteVariant, judgment: Judgment, target_time: float):
    if not Options.sfx_enabled:
        return
    effect = note_hit_sfx(variant, judgment)
    if effect.id == 0:
        return
    effect.schedule(target_time, SFX_DISTANCE)


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

    @property
    def is_active(self):
        return self.handle.id != 0

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

    def take(self, other: HoldHandle):
        if self != other:
            self.destroy()
            self.handle = other.handle
        other.handle.id = 0
