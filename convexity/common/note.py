from __future__ import annotations

from enum import IntEnum
from math import floor, log, pi

from sonolus.script.bucket import Judgment, JudgmentWindow
from sonolus.script.easing import (
    ease_in_out_cubic,
    ease_in_out_sine,
    ease_out_cubic,
    ease_out_quad,
)
from sonolus.script.effect import Effect
from sonolus.script.globals import level_memory
from sonolus.script.interval import lerp, remap, unlerp
from sonolus.script.particle import Particle, ParticleHandle
from sonolus.script.quad import Quad
from sonolus.script.record import Record
from sonolus.script.runtime import is_skip, time
from sonolus.script.sprite import Sprite
from sonolus.script.timing import beat_to_bpm, beat_to_time
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
    note_particle_circular_layout,
    note_particle_linear_layout,
    preempt_time,
    sim_line_layout,
    transform_quad,
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


def note_body_sprite(variant: NoteVariant, direction: float):
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


def note_arrow_sprite(variant: NoteVariant, direction: float):
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
        case NoteVariant.HOLD_START | NoteVariant.HOLD_END | NoteVariant.HOLD_TICK:
            result @= Skin.hold_arrow
    return result


def note_head_sprite(variant: NoteVariant):
    return copy(Skin.hold_start_note)


def note_connector_sprite(variant: NoteVariant):
    return copy(Skin.connector)


def note_particle_linear(variant: NoteVariant, direction: float):
    result = copy(Particles.tap_linear)
    match variant:
        case NoteVariant.SINGLE:
            result @= Particles.tap_linear
        case NoteVariant.HOLD_START:
            result @= Particles.hold_linear
        case NoteVariant.HOLD_END:
            result @= Particles.hold_linear
        case NoteVariant.HOLD_TICK:
            result @= Particles.hold_linear
        case NoteVariant.FLICK:
            result @= Particles.flick_linear
        case NoteVariant.DIRECTIONAL_FLICK:
            if direction > 0:
                result @= Particles.right_flick_linear
            else:
                result @= Particles.left_flick_linear
        case NoteVariant.SWING:
            result @= Particles.swing_linear
    return result


def note_hold_particle_linear(variant: NoteVariant):
    return copy(Particles.hold_active_linear)


def note_particle_circular(variant: NoteVariant, direction: float):
    result = copy(Particles.tap_circular)
    match variant:
        case NoteVariant.SINGLE:
            result @= Particles.tap_circular
        case NoteVariant.HOLD_START:
            result @= Particles.hold_circular
        case NoteVariant.HOLD_END:
            result @= Particles.hold_circular
        case NoteVariant.HOLD_TICK:
            result @= Particles.hold_circular
        case NoteVariant.FLICK:
            result @= Particles.flick_circular
        case NoteVariant.DIRECTIONAL_FLICK:
            if direction > 0:
                result @= Particles.right_flick_circular
            else:
                result @= Particles.left_flick_circular
        case NoteVariant.SWING:
            result @= Particles.swing_circular
    return result


def note_hold_particle_circular(variant: NoteVariant):
    return copy(Particles.hold_active_circular)


def y_to_alpha(y: float):
    progress = unlerp(
        Layout.lane_length,
        0,
        y,
    )
    if Options.extend_lanes and 0.0 <= progress <= 0.2:
        result = ease_out_cubic(remap(0.0, 0.2, 0, 1, progress))
    elif Options.hidden != 0 and progress > 1 - Options.hidden - 0.1:
        result = ease_out_cubic(remap(1 - Options.hidden - 0.1, 1 - Options.hidden + 0.1, 1, 0, progress))
    else:
        result = 1
    if Options.blink:
        beat = current_beat()
        factor = 2 ** floor(log(240 / beat_to_bpm(beat) / log(2)))
        blink_progress = 1 - abs(beat * factor - round(beat * factor)) * 2
        result *= ease_in_out_sine(remap(0.4, 0.8, 0, 1, blink_progress))
    return result


def draw_note_body(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return
    layout = note_layout(pos, y)
    sprite.draw(layout, z=Layer.NOTE - y + pos.mid / 1000, a=y_to_alpha(y))


def draw_note_head(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return
    layout = note_layout(pos, y)
    sprite.draw(layout, z=Layer.NOTE_HEAD - y + pos.mid / 1000, a=y_to_alpha(y))


def draw_note_connector(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
    prev_pos: LanePosition,
    prev_y: float,
):
    if Options.boxy_sliders and pos != prev_pos:
        scaled_pos = pos.scale_centered(Options.note_size)
        scaled_prev_pos = prev_pos.scale_centered(Options.note_size)
        horizontal_height = min(0.5, abs(y - prev_y))
        vertical_direction = 1 if y > prev_y else -1
        horizontal_pos = LanePosition(
            min(scaled_pos.left, scaled_prev_pos.left), max(scaled_pos.right, scaled_prev_pos.right)
        )
        if scaled_pos.right == horizontal_pos.right:
            horizontal_pos.right = scaled_pos.left
        elif scaled_pos.left == horizontal_pos.left:
            horizontal_pos.left = scaled_pos.right
        horizontal_y = prev_y + vertical_direction * horizontal_height
        _draw_horizontal_note_connector(
            sprite,
            horizontal_pos,
            horizontal_y,
            prev_y,
        )
        _draw_note_connector(
            sprite,
            pos,
            y,
            pos,
            prev_y,
        )
    else:
        _draw_note_connector(sprite, pos, y, prev_pos, prev_y)


def _draw_note_connector(
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

    pos = pos.scale_centered(Options.connector_width)
    prev_pos = prev_pos.scale_centered(Options.connector_width)

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
            z=Layer.CONNECTOR - y + pos.mid / 1000,
            a=Options.connector_alpha * y_to_alpha((segment_y + segment_prev_y) / 2),
        )


def _draw_horizontal_note_connector(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
    prev_y: float,
):
    if prev_y < Layout.min_safe_y and y < Layout.min_safe_y:
        return
    if prev_y > Layout.lane_length and y > Layout.lane_length:
        return

    if abs(prev_y - y) < EPSILON:
        y = prev_y - EPSILON

    tl = Vec2(pos.left, y)
    tr = Vec2(pos.right, y)
    bl = Vec2(pos.left, prev_y)
    br = Vec2(pos.right, prev_y)

    arc_quality = Options.arc_quality
    n_segments = floor(abs(pos.left - pos.right) * arc_quality * Options.arc) + 1
    for i in range(n_segments):
        segment_tl = lerp(tl, tr, i / n_segments)
        segment_tr = lerp(tl, tr, (i + 1) / n_segments)
        segment_bl = lerp(bl, br, i / n_segments)
        segment_br = lerp(bl, br, (i + 1) / n_segments)
        base = Quad(
            bl=segment_bl,
            br=segment_br,
            tl=segment_tl,
            tr=segment_tr,
        )
        sprite.draw(
            transform_quad(base),
            z=Layer.CONNECTOR - y + pos.mid / 1000,
            a=Options.connector_alpha * y_to_alpha((segment_bl.y + segment_br.y) / 2),
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
            layout,
            z=Layer.SIM_LINE - y + pos.mid / 1000,
            a=y_to_alpha((segment_y + segment_prev_y) / 2) * Options.sim_line_alpha,
        )


def draw_note_arrow(
    sprite: Sprite,
    direction: float,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return

    period = 0.3
    count = max(abs(direction), 1)
    lane_offset = 0
    if Options.alt_side_flicks:
        if direction > 0:
            lane_offset = -0.5
        elif direction < 0:
            lane_offset = 0.5
    elif direction > 0:
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
        if direction == 0 or Options.alt_side_flicks:
            y_offset = lerp(0.0, 0.5, progress) if direction == 0 else 0.0
            base_bl = transform_vec(Vec2(lane - 0.5 * Options.note_size, y))
            base_br = transform_vec(Vec2(lane + 0.5 * Options.note_size, y))
            ort = (base_br - base_bl).orthogonal()
            bl = base_bl + ort * y_offset
            br = base_br + ort * y_offset
            tl = bl + ort
            tr = br + ort
            up_layout = Quad(
                bl=bl,
                br=br,
                tl=tl,
                tr=tr,
            )
            if direction > 0:
                layout @= Quad(
                    bl=up_layout.tl,
                    br=up_layout.bl,
                    tl=up_layout.tr,
                    tr=up_layout.br,
                )
            elif direction < 0:
                layout @= Quad(
                    bl=up_layout.br,
                    br=up_layout.tr,
                    tl=up_layout.bl,
                    tr=up_layout.tl,
                )
            else:
                layout @= up_layout
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
        sprite.draw(layout, z=Layer.ARROW - y + pos.mid / 1000, a=alpha * y_to_alpha(y))


def draw_swing_arrow(
    sprite: Sprite,
    direction: float,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return

    y_offset = 0.4 if Options.vertical_notes or Options.stage_tilt == 0 else 0
    lane = pos.mid
    base_bl = transform_vec(Vec2(lane - 0.5 * Options.note_size, y))
    base_br = transform_vec(Vec2(lane + 0.5 * Options.note_size, y))
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
    sprite.draw(layout, z=Layer.ARROW - y + lane / 1000, a=y_to_alpha(y))


def flick_velocity_threshold(direction: float = 0):
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
    note_particle_linear: Particle,
    note_particle_circular: Particle,
    pos: LanePosition,
    judgment: Judgment,
):
    play_hit_sfx(variant, judgment)
    play_hit_particle(note_particle_linear, note_particle_circular, pos)


def play_watch_hit_effects(
    note_particle_linear: Particle,
    note_particle_circular: Particle,
    pos: LanePosition,
):
    play_hit_particle(note_particle_linear, note_particle_circular, pos)


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
    note_particle_linear: Particle,
    note_particle_circular: Particle,
    pos: LanePosition,
):
    if Options.note_effect_linear_enabled:
        note_particle_linear.spawn(
            note_particle_linear_layout(pos),
            duration=0.5,
        )
    if Options.note_effect_circular_enabled:
        note_particle_circular.spawn(
            note_particle_circular_layout(pos),
            duration=0.5,
        )
    if Options.lane_effect_enabled:
        Particles.lane.spawn(
            lane_layout(pos),
            duration=0.2,
        )


class HoldHandle(Record):
    handle_linear: ParticleHandle
    handle_circular: ParticleHandle

    @property
    def is_active(self):
        return self.handle_linear.id != 0

    def update(self, particle_linear: Particle, particle_circular: Particle, pos: LanePosition):
        if self.handle_linear.id == 0:
            self.handle_linear @= particle_linear.spawn(
                note_particle_linear_layout(pos),
                duration=1.0,
                loop=True,
            )
            self.handle_circular @= particle_circular.spawn(
                note_particle_linear_layout(pos),
                duration=1.0,
                loop=True,
            )
        else:
            self.handle_linear.move(note_particle_linear_layout(pos))
            self.handle_circular.move(note_particle_circular_layout(pos))

    def destroy(self):
        if self.handle_linear.id != 0:
            self.handle_linear.destroy()
            self.handle_linear.id = 0
            self.handle_circular.destroy()
            self.handle_circular.id = 0

    def destroy_silent(self):
        self.handle_linear.destroy()
        self.handle_circular.destroy()

    def take(self, other: HoldHandle):
        if self != other:
            self.destroy()
            self.handle_linear = other.handle_linear
            self.handle_circular = other.handle_circular
        other.handle_linear.id = 0
        other.handle_circular.id = 0


@level_memory
class ScaledTimeState:
    beat: float


def pulse_note_times(beat: float) -> tuple[float, float]:
    target_time = pulse_beat_to_time(beat)
    return beat_to_time(beat) - 2 * preempt_time(), target_time


def pulse_scaled_time() -> float:
    beat = current_beat()
    return pulse_beat_to_time(beat)


def pulse_beat_to_time(beat: float) -> float:
    return beat_to_time(pulse_adjust_beat(beat))


def pulse_adjust_beat(beat: float) -> float:
    n = 1
    nbeat = n * beat
    return (float(floor(nbeat)) + pulse_ease(nbeat % 1)) / n


def pulse_ease(n: float):
    a = 0.4
    return n * a + (1 - a) * ease_in_out_sine(n)


def wave_note_times(beat: float) -> tuple[float, float]:
    target_time = beat_to_time(beat)
    return target_time - 2 * preempt_time(), target_time


def wave_scaled_time(target_beat: float) -> float:
    beat = current_beat()
    diff = target_beat - beat
    adjusted_beat = target_beat - wave_adjust_beat(diff)
    return beat_to_time(adjusted_beat)


def wave_adjust_beat(beat: float) -> float:
    n = 2
    nbeat = n * beat
    return (float(floor(nbeat)) + wave_ease(nbeat % 1)) / n


def wave_ease(n: float):
    a = 0.3
    return n * a + (1 - a) * ease_in_out_cubic(n)


def current_beat() -> float:
    return ScaledTimeState.beat


def update_current_beat() -> float:
    if is_skip():
        ScaledTimeState.beat = 0
    if time() <= 0:
        return time() * beat_to_bpm(0) / 60
    beat = ScaledTimeState.beat
    while abs(beat_to_time(beat) - time()) > 1e-4:
        delta = time() - beat_to_time(beat)
        beat += delta * beat_to_bpm(beat) / 60
    ScaledTimeState.beat = beat
    return beat
