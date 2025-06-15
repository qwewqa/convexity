from math import pi

from sonolus.script.interval import lerp, lerp_clamped
from sonolus.script.quad import Rect
from sonolus.script.runtime import (
    tutorial_ui_configs as ui_configs,
)
from sonolus.script.vec import Vec2

from convexity.common.layout import Layout, lane_to_pos, transform_vec
from convexity.tutorial.instructions import InstructionIcons


def progress_to_y(p: float) -> float:
    return lerp(Layout.lane_length, 0, p)


def note_center_pos(y: float, lane: float) -> Vec2:
    pos = lane_to_pos(lane)
    ml = transform_vec(Vec2(pos.left, y))
    mr = transform_vec(Vec2(pos.right, y))
    return (ml + mr) / 2


def note_side_vec(y: float, lane: float) -> Vec2:
    pos = lane_to_pos(lane)
    ml = transform_vec(Vec2(pos.left, y))
    mr = transform_vec(Vec2(pos.right, y))
    return (mr - ml).normalize()


def paint_tap_motion(
    pos: Vec2,
    a: float,
    progress: float,
):
    angle = lerp_clamped(pi / 6, pi / 3, progress)
    position = Vec2(0, -1).rotate(pi / 3) * (0.25 * ui_configs.instruction.scale) + pos
    InstructionIcons.hand.paint(
        position=Vec2(0, 1).rotate(angle) * 0.25 * ui_configs.instruction.scale + position,
        size=0.25 * ui_configs.instruction.scale,
        rotation=(180 * angle) / pi,
        z=0,
        a=a * ui_configs.instruction.alpha,
    )


def paint_slide_motion(
    from_pos: Vec2,
    to_pos: Vec2,
    a: float,
    progress: float,
):
    pos = lerp_clamped(from_pos, to_pos, progress)
    InstructionIcons.hand.paint(
        position=pos,
        size=0.25 * ui_configs.instruction.scale,
        rotation=(180 * pi / 3) / pi,
        z=0,
        a=a * ui_configs.instruction.alpha,
    )


def intro_note_layout(
    y: float,
    lane: float = 0,
):
    size = 0.6
    base_y = 0.2
    return Rect.from_center(Vec2(lane * size, base_y + y * size), Vec2(size, size)).as_quad()
