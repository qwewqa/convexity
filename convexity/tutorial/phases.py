from math import pi

from sonolus.script.bucket import Judgment
from sonolus.script.easing import ease_in_quad
from sonolus.script.globals import level_memory
from sonolus.script.instruction import clear_instruction
from sonolus.script.interval import Interval, lerp, remap_clamped
from sonolus.script.quad import Quad
from sonolus.script.runtime import delta_time, time
from sonolus.script.vec import Vec2

from convexity.common.layout import Layer, lane_to_pos, note_particle_layout
from convexity.common.note import (
    NoteVariant,
    draw_note_arrow,
    draw_note_body,
    draw_note_connector,
    draw_note_head,
    draw_swing_arrow,
    note_arrow_sprite,
    note_body_sprite,
    note_connector_sprite,
    note_head_sprite,
    note_hit_sfx,
    note_particle,
)
from convexity.common.options import Options
from convexity.tutorial.instructions import Instructions
from convexity.tutorial.note import (
    intro_note_layout,
    note_center_pos,
    note_side_vec,
    paint_slide_motion,
    paint_tap_motion,
    progress_to_y,
)


@level_memory
class TutorialState:
    phase_start_time: float
    tutorial_phase: int
    phase_update: bool


def phase_time():
    return time() - TutorialState.phase_start_time


def time_is(t: float):
    return phase_time() - delta_time() < t <= phase_time()


def get_part_progress(progress: float, parts: int) -> float:
    if progress >= 1:
        # Avoids some floating point error
        return 1
    if progress <= 0:
        return 0
    return progress * parts % 1


def single_note_phase() -> bool:
    lane = 0
    body_sprite = note_body_sprite(NoteVariant.SINGLE, 0)
    hit_particle = note_particle(NoteVariant.SINGLE, 0)
    effect = note_hit_sfx(NoteVariant.SINGLE, Judgment.PERFECT)

    intro_interval = Interval.zero().then(1)
    fall_interval = intro_interval.then(2)
    frozen_interval = fall_interval.then(1 * 4)
    hit_interval = frozen_interval.then(1)

    if phase_time() in intro_interval:
        body_sprite.draw(
            intro_note_layout(0),
            z=Layer.NOTE,
        )
    elif phase_time() in fall_interval:
        progress = fall_interval.unlerp(phase_time())
        y = progress_to_y(progress)
        draw_note_body(
            body_sprite,
            pos=lane_to_pos(lane),
            y=y,
        )
    elif phase_time() in frozen_interval:
        progress = frozen_interval.unlerp(phase_time())
        y = progress_to_y(1)
        parts = 4
        part_progress = get_part_progress(progress, parts)
        if time_is(frozen_interval.start):
            Instructions.tap.show()
        draw_note_body(
            body_sprite,
            pos=lane_to_pos(lane),
            y=y,
        )
        a = remap_clamped(0.75, 1, 1, 0, part_progress)
        tap_progress = remap_clamped(0.25, 0.75, 0, 1, part_progress)
        paint_tap_motion(
            note_center_pos(y, lane),
            a,
            tap_progress,
        )
    elif phase_time() in hit_interval:
        if time_is(hit_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(lane_to_pos(lane)),
                1,
            )
            effect.play()
    else:
        return False
    return True


def swing_note_phase() -> bool:
    lane = 0
    body_sprite = note_body_sprite(NoteVariant.SWING, 1)
    arrow_sprite = note_arrow_sprite(NoteVariant.SWING, 1)
    hit_particle = note_particle(NoteVariant.SWING, 1)
    effect = note_hit_sfx(NoteVariant.SWING, Judgment.PERFECT)

    intro_interval = Interval.zero().then(1)
    fall_interval = intro_interval.then(2)
    frozen_interval = fall_interval.then(1 * 4)
    hit_interval = frozen_interval.then(1)

    if phase_time() in intro_interval:
        body_sprite.draw(
            intro_note_layout(-0.5),
            z=Layer.NOTE,
        )
        arrow_sprite.draw(
            intro_note_layout(0.4).rotate_centered(-pi / 2),
            z=Layer.ARROW,
        )
    elif phase_time() in fall_interval:
        progress = fall_interval.unlerp(phase_time())
        y = progress_to_y(progress)
        pos = lane_to_pos(lane)
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_swing_arrow(
            arrow_sprite,
            direction=1,
            pos=pos,
            y=y,
        )
    elif phase_time() in frozen_interval:
        progress = frozen_interval.unlerp(phase_time())
        y = progress_to_y(1)
        pos = lane_to_pos(lane)
        parts = 4
        part_progress = get_part_progress(progress, parts)
        if time_is(frozen_interval.start):
            Instructions.slide.show()
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_swing_arrow(
            arrow_sprite,
            direction=1,
            pos=pos,
            y=y,
        )
        a = remap_clamped(0.75, 1, 1, 0, part_progress)
        paint_slide_motion(
            note_center_pos(y, lane) - Vec2(0.4, 0),
            note_center_pos(y, lane) + Vec2(0.4, 0),
            a,
            part_progress,
        )
    elif phase_time() in hit_interval:
        pos = lane_to_pos(lane)
        if time_is(hit_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(pos),
                1,
            )
            effect.play()
    else:
        return False
    return True


def flick_note_phase() -> bool:
    lane = 0
    body_sprite = note_body_sprite(NoteVariant.FLICK, 0)
    arrow_sprite = note_arrow_sprite(NoteVariant.FLICK, 0)
    hit_particle = note_particle(NoteVariant.FLICK, 0)
    effect = note_hit_sfx(NoteVariant.FLICK, Judgment.PERFECT)

    intro_interval = Interval.zero().then(1)
    fall_interval = intro_interval.then(2)
    frozen_interval = fall_interval.then(1.43 * 4)
    hit_interval = frozen_interval.then(1)

    if phase_time() in intro_interval:
        body_sprite.draw(
            intro_note_layout(-0.5),
            z=Layer.NOTE,
        )
        arrow_sprite.draw(
            intro_note_layout(0.4),
            z=Layer.ARROW,
        )
    elif phase_time() in fall_interval:
        progress = fall_interval.unlerp(phase_time())
        y = progress_to_y(progress)
        pos = lane_to_pos(lane)
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_arrow(
            arrow_sprite,
            direction=0,
            pos=pos,
            y=y,
        )
    elif phase_time() in frozen_interval:
        progress = frozen_interval.unlerp(phase_time())
        y = progress_to_y(1)
        pos = lane_to_pos(lane)
        parts = 4
        part_progress = get_part_progress(progress, parts)
        tap_progress = remap_clamped(0, 0.7, 0, 1, part_progress)
        swipe_progress = remap_clamped(0.7, 1, 0, 1, part_progress)
        if time_is(frozen_interval.start):
            Instructions.tap_flick.show()
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_arrow(
            arrow_sprite,
            direction=0,
            pos=pos,
            y=y,
        )
        if tap_progress < 1:
            a = 1
            tap_progress = remap_clamped(0.25, 0.75, 0, 1, tap_progress)
            paint_tap_motion(
                note_center_pos(y, lane),
                a,
                tap_progress,
            )
        else:
            a = remap_clamped(0.6, 1, 1, 0, swipe_progress)
            paint_slide_motion(
                note_center_pos(y, lane),
                note_center_pos(y, lane) + Vec2(0, 0.7),
                a,
                ease_in_quad(swipe_progress),
            )
    elif phase_time() in hit_interval:
        pos = lane_to_pos(lane)
        if time_is(hit_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(pos),
                1,
            )
            effect.play()
    else:
        return False
    return True


def hold_start_note_phase() -> bool:
    lane = 0
    tick_lane = 2
    tick_sprite = note_body_sprite(NoteVariant.HOLD_TICK, 0)
    head_sprite = note_head_sprite(NoteVariant.HOLD_START)
    body_sprite = note_body_sprite(NoteVariant.HOLD_START, 0)
    connector_sprite = note_connector_sprite(NoteVariant.HOLD_START)
    hit_particle = note_particle(NoteVariant.HOLD_START, 0)
    effect = note_hit_sfx(NoteVariant.HOLD_START, Judgment.PERFECT)

    intro_interval = Interval.zero().then(1)
    fall_interval = intro_interval.then(2)
    frozen_interval = fall_interval.then(1 * 4)
    follow_interval = frozen_interval.then(1)
    end_interval = follow_interval.then(1)

    if phase_time() in intro_interval:
        body_layout = intro_note_layout(-0.5)
        body_sprite.draw(
            body_layout,
            z=Layer.NOTE,
        )
        connector_bl = (body_layout.tl + body_layout.bl) / 2
        connector_br = (body_layout.tr + body_layout.br) / 2
        ort = (connector_br - connector_bl).orthogonal()
        connector_tl = connector_bl + ort
        connector_tr = connector_br + ort
        connector_sprite.draw(
            Quad(bl=connector_bl, br=connector_br, tl=connector_tl, tr=connector_tr),
            z=Layer.CONNECTOR,
            a=Options.connector_alpha,
        )
    elif phase_time() in fall_interval:
        progress = fall_interval.unlerp(phase_time())
        y = progress_to_y(progress)
        pos = lane_to_pos(lane)
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_connector(
            connector_sprite,
            pos=lane_to_pos(lerp(lane, tick_lane, progress)),
            y=progress_to_y(0),
            prev_pos=pos,
            prev_y=y,
        )
    elif phase_time() in frozen_interval:
        progress = frozen_interval.unlerp(phase_time())
        y = progress_to_y(1)
        pos = lane_to_pos(lane)
        parts = 4
        part_progress = get_part_progress(progress, parts)
        if time_is(frozen_interval.start):
            Instructions.hold.show()
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_connector(
            connector_sprite,
            pos=lane_to_pos(tick_lane),
            y=progress_to_y(0),
            prev_pos=pos,
            prev_y=y,
        )
        a = remap_clamped(0.75, 1, 1, 0, part_progress)
        tap_progress = remap_clamped(0.25, 0.75, 0, 1, part_progress)
        paint_tap_motion(
            note_center_pos(y, lane),
            a,
            tap_progress,
        )
    elif phase_time() in follow_interval:
        pos = lane_to_pos(lane)
        if time_is(follow_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(pos),
                1,
            )
            effect.play()
        progress = follow_interval.unlerp(phase_time())
        tick_y = progress_to_y(progress)
        tick_pos = lane_to_pos(tick_lane)
        head_lane = lerp(lane, tick_lane, progress)
        head_pos = lane_to_pos(head_lane)
        draw_note_body(
            tick_sprite,
            pos=tick_pos,
            y=tick_y,
        )
        draw_note_head(
            head_sprite,
            pos=head_pos,
            y=progress_to_y(1),
        )
        draw_note_connector(
            connector_sprite,
            pos=tick_pos,
            y=tick_y,
            prev_pos=head_pos,
            prev_y=progress_to_y(1),
        )
        draw_note_connector(
            connector_sprite,
            pos=tick_pos,
            y=progress_to_y(0),
            prev_pos=tick_pos,
            prev_y=tick_y,
        )
        paint_tap_motion(
            note_center_pos(0, head_lane),
            1,
            1,
        )
    elif phase_time() in end_interval:
        pos = lane_to_pos(tick_lane)
        if time_is(end_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(pos),
                1,
            )
            effect.play()
        draw_note_head(
            head_sprite,
            pos=pos,
            y=progress_to_y(1),
        )
        draw_note_connector(
            connector_sprite,
            pos=pos,
            y=progress_to_y(0),
            prev_pos=pos,
            prev_y=progress_to_y(1),
        )
        paint_tap_motion(
            note_center_pos(0, tick_lane),
            1,
            1,
        )
    else:
        return False
    return True


def hold_end_note_phase() -> bool:
    lane = 0
    body_sprite = note_body_sprite(NoteVariant.HOLD_END, 0)
    connector_sprite = note_connector_sprite(NoteVariant.HOLD_END)
    head_sprite = note_head_sprite(NoteVariant.HOLD_END)
    hit_particle = note_particle(NoteVariant.HOLD_END, 0)
    effect = note_hit_sfx(NoteVariant.HOLD_END, Judgment.PERFECT)

    intro_interval = Interval.zero().then(1)
    fall_interval = intro_interval.then(2)
    frozen_interval = fall_interval.then(1 * 4)
    hit_interval = frozen_interval.then(1)

    if phase_time() in intro_interval:
        body_layout = intro_note_layout(0)
        body_sprite.draw(
            body_layout,
            z=Layer.NOTE,
        )
        connector_tl = (body_layout.tl + body_layout.bl) / 2
        connector_tr = (body_layout.tr + body_layout.br) / 2
        ort = (connector_tr - connector_tl).orthogonal()
        connector_bl = connector_tl - ort
        connector_br = connector_tr - ort
        connector_sprite.draw(
            Quad(bl=connector_bl, br=connector_br, tl=connector_tl, tr=connector_tr),
            z=Layer.CONNECTOR,
            a=Options.connector_alpha,
        )
    elif phase_time() in fall_interval:
        progress = fall_interval.unlerp(phase_time())
        y = progress_to_y(progress)
        pos = lane_to_pos(lane)
        draw_note_head(
            head_sprite,
            pos=pos,
            y=progress_to_y(1),
        )
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_connector(
            connector_sprite,
            pos=pos,
            y=y,
            prev_pos=pos,
            prev_y=progress_to_y(1),
        )
        paint_tap_motion(
            note_center_pos(0, lane),
            1,
            1,
        )
    elif phase_time() in frozen_interval:
        progress = frozen_interval.unlerp(phase_time())
        y = progress_to_y(1)
        pos = lane_to_pos(lane)
        parts = 4
        part_progress = get_part_progress(progress, parts)
        if time_is(frozen_interval.start):
            Instructions.release.show()
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        a = remap_clamped(0.5, 0.75, 1, 0, part_progress)
        release_progress = remap_clamped(0.25, 0.75, 0, 1, part_progress)
        paint_tap_motion(
            note_center_pos(y, lane),
            a,
            (1 - release_progress),
        )
    elif phase_time() in hit_interval:
        pos = lane_to_pos(lane)
        if time_is(hit_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(pos),
                1,
            )
            effect.play()
    else:
        return False
    return True


def hold_flick_note_phase() -> bool:
    lane = 0
    body_sprite = note_body_sprite(NoteVariant.FLICK, 0)
    arrow_sprite = note_arrow_sprite(NoteVariant.FLICK, 0)
    connector_sprite = note_connector_sprite(NoteVariant.FLICK)
    head_sprite = note_head_sprite(NoteVariant.FLICK)
    hit_particle = note_particle(NoteVariant.FLICK, 0)
    effect = note_hit_sfx(NoteVariant.FLICK, Judgment.PERFECT)

    intro_interval = Interval.zero().then(1)
    fall_interval = intro_interval.then(2)
    frozen_interval = fall_interval.then(1.43 * 4)
    hit_interval = frozen_interval.then(1)

    if phase_time() in intro_interval:
        body_layout = intro_note_layout(-0.3)
        body_sprite.draw(
            body_layout,
            z=Layer.NOTE,
        )
        arrow_sprite.draw(
            intro_note_layout(0.6),
            z=Layer.ARROW,
        )
        connector_tl = (body_layout.tl + body_layout.bl) / 2
        connector_tr = (body_layout.tr + body_layout.br) / 2
        ort = (connector_tr - connector_tl).orthogonal()
        connector_bl = connector_tl - ort
        connector_br = connector_tr - ort
        connector_sprite.draw(
            Quad(bl=connector_bl, br=connector_br, tl=connector_tl, tr=connector_tr),
            z=Layer.CONNECTOR,
            a=Options.connector_alpha,
        )
    elif phase_time() in fall_interval:
        progress = fall_interval.unlerp(phase_time())
        y = progress_to_y(progress)
        pos = lane_to_pos(lane)
        draw_note_head(
            head_sprite,
            pos=pos,
            y=progress_to_y(1),
        )
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_arrow(
            arrow_sprite,
            direction=0,
            pos=pos,
            y=y,
        )
        draw_note_connector(
            connector_sprite,
            pos=pos,
            y=y,
            prev_pos=pos,
            prev_y=progress_to_y(1),
        )
        paint_tap_motion(
            note_center_pos(0, lane),
            1,
            1,
        )
    elif phase_time() in frozen_interval:
        progress = frozen_interval.unlerp(phase_time())
        y = progress_to_y(1)
        pos = lane_to_pos(lane)
        parts = 4
        part_progress = get_part_progress(progress, parts)
        hold_progress = remap_clamped(0, 0.7, 0, 1, part_progress)
        swipe_progress = remap_clamped(0.7, 1, 0, 1, part_progress)
        if time_is(frozen_interval.start):
            Instructions.hold_flick.show()
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_arrow(
            arrow_sprite,
            direction=0,
            pos=pos,
            y=progress_to_y(1),
        )
        if hold_progress < 1:
            paint_tap_motion(
                note_center_pos(y, lane),
                1,
                1,
            )
        else:
            a = remap_clamped(0.6, 1, 1, 0, swipe_progress)
            paint_slide_motion(
                note_center_pos(y, lane),
                note_center_pos(y, lane) + Vec2(0, 0.7),
                a,
                ease_in_quad(swipe_progress),
            )
    elif phase_time() in hit_interval:
        pos = lane_to_pos(lane)
        if time_is(hit_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(pos),
                1,
            )
            effect.play()
    else:
        return False
    return True


def directional_note_phase(lane: int, direction: float) -> bool:
    direction_sign = 1 if direction > 0 else -1
    body_sprite = note_body_sprite(NoteVariant.DIRECTIONAL_FLICK, direction)
    arrow_sprite = note_arrow_sprite(NoteVariant.DIRECTIONAL_FLICK, direction)
    hit_particle = note_particle(NoteVariant.DIRECTIONAL_FLICK, direction)
    effect = note_hit_sfx(NoteVariant.DIRECTIONAL_FLICK, Judgment.PERFECT)

    intro_interval = Interval.zero().then(1)
    fall_interval = intro_interval.then(2)
    frozen_interval = fall_interval.then(1.43 * 4)
    hit_interval = frozen_interval.then(1)

    if phase_time() in intro_interval:
        body_sprite.draw(
            intro_note_layout(0, lane),
            z=Layer.NOTE,
        )
        for i in range(abs(direction)):
            arrow_sprite.draw(
                intro_note_layout(0, lane + (i + 1) * direction_sign).rotate_centered(-pi / 2 * direction_sign),
                z=Layer.ARROW,
            )
    elif phase_time() in fall_interval:
        progress = fall_interval.unlerp(phase_time())
        y = progress_to_y(progress)
        pos = lane_to_pos(lane)
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_arrow(
            arrow_sprite,
            direction=direction,
            pos=pos,
            y=y,
        )
    elif phase_time() in frozen_interval:
        progress = frozen_interval.unlerp(phase_time())
        y = progress_to_y(1)
        pos = lane_to_pos(lane)
        parts = 4
        part_progress = get_part_progress(progress, parts)
        tap_progress = remap_clamped(0, 0.7, 0, 1, part_progress)
        swipe_progress = remap_clamped(0.7, 1, 0, 1, part_progress)
        if time_is(frozen_interval.start):
            Instructions.tap_flick.show()
        draw_note_body(
            body_sprite,
            pos=pos,
            y=y,
        )
        draw_note_arrow(
            arrow_sprite,
            direction=direction,
            pos=pos,
            y=y,
        )
        if tap_progress < 1:
            a = 1
            tap_progress = remap_clamped(0.25, 0.75, 0, 1, tap_progress)
            paint_tap_motion(
                note_center_pos(y, lane),
                a,
                tap_progress,
            )
        else:
            a = remap_clamped(0.6, 1, 1, 0, swipe_progress)
            paint_slide_motion(
                note_center_pos(y, lane),
                note_center_pos(y, lane) + note_side_vec(y, lane) * 0.7 * direction_sign,
                a,
                ease_in_quad(swipe_progress),
            )
    elif phase_time() in hit_interval:
        pos = lane_to_pos(lane)
        if time_is(hit_interval.start):
            clear_instruction()
            hit_particle.spawn(
                note_particle_layout(pos),
                1,
            )
            effect.play()
    else:
        return False
    return True


def combined_directional_note_phase():
    a = directional_note_phase(-1, -1)
    b = directional_note_phase(1, 1)
    return a or b


tutorial_phases = (
    single_note_phase,
    swing_note_phase,
    flick_note_phase,
    hold_start_note_phase,
    hold_end_note_phase,
    hold_flick_note_phase,
    combined_directional_note_phase,
)
