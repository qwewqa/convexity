from enum import IntEnum
from typing import Self

from sonolus.script.globals import level_memory
from sonolus.script.interval import clamp, lerp, remap, unlerp
from sonolus.script.quad import Quad, Rect
from sonolus.script.record import Record
from sonolus.script.transform import Transform2d
from sonolus.script.vec import Vec2

EPSILON = 1e-4


class Layer(IntEnum):
    STAGE = 0
    LANE = 1
    SLOT = 2
    JUDGE_LINE = 3

    CONNECTOR = 1000
    NOTE = 2000


@level_memory
class Layout:
    vanishing_point: Vec2

    scale: float

    judge_line_y: float
    lane_height: float
    note_height: float
    particle_height: float

    stage_border_width: float

    lane_transform: Transform2d
    min_safe_y: float


def init_layout():
    Layout.vanishing_point = Vec2(0, 1.8)

    Layout.scale = 0.5

    Layout.judge_line_y = -0.6
    Layout.lane_height = 8
    Layout.note_height = 1.0
    Layout.particle_height = 0.5

    Layout.stage_border_width = 0.125

    compute_layout()


def compute_layout():
    Layout.lane_transform @= (
        Transform2d.new()
        .scale(Vec2(Layout.scale, Layout.scale))
        .perspective_y(Layout.judge_line_y, Layout.vanishing_point)
    )

    # Below this coordinate, points are "behind" the screen so they shouldn't be displayed.
    # We add half of the note height to make this the safe note center y-coordinate.
    Layout.min_safe_y = (
        Layout.judge_line_y
        - Layout.vanishing_point.y
        + Layout.note_height / 2
        + EPSILON
    )


class LanePosition(Record):
    left: float
    right: float

    @property
    def mid(self) -> float:
        return (self.left + self.right) / 2

    def __add__(self, other: Self) -> Self:
        return LanePosition(left=self.left + other.left, right=self.right + other.right)

    def __sub__(self, other: Self) -> Self:
        return LanePosition(left=self.left - other.left, right=self.right - other.right)

    def __mul__(self, other: float) -> Self:
        return LanePosition(left=self.left * other, right=self.right * other)

    def __truediv__(self, other: float) -> Self:
        return LanePosition(left=self.left / other, right=self.right / other)


def lane_layout(pos: LanePosition) -> Quad:
    base = Rect(l=pos.left, r=pos.right, b=Layout.min_safe_y, t=Layout.lane_height)
    return Layout.lane_transform.transform_quad(base)


def note_layout(pos: LanePosition, y: float) -> Quad:
    base = Rect(
        l=pos.left,
        r=pos.right,
        b=y - Layout.note_height / 2,
        t=y + Layout.note_height / 2,
    )
    return Layout.lane_transform.transform_quad(base)


def note_particle_layout(pos: LanePosition, scale: float) -> Rect:
    bl = Layout.lane_transform.transform_vec(Vec2(pos.left, 0))
    br = Layout.lane_transform.transform_vec(Vec2(pos.right, 0))
    height = Layout.scale * scale
    return Rect(l=bl.x, r=br.x, b=bl.y, t=bl.y + height)


def connector_layout(
    pos: LanePosition,
    y: float,
    prev_pos: LanePosition,
    prev_y: float,
) -> Quad:
    if abs(prev_y - y) < EPSILON:
        y = prev_y - EPSILON
    clamped_prev_y = clamp_y_to_stage(prev_y)
    clamped_y = clamp_y_to_stage(y)
    clamped_prev_pos = lerp(
        prev_pos,
        pos,
        unlerp(prev_y, y, clamped_prev_y),
    )
    clamped_pos = lerp(
        prev_pos,
        pos,
        unlerp(prev_y, y, clamped_y),
    )
    base = Quad(
        bl=Vec2(clamped_prev_pos.left, clamped_prev_y),
        br=Vec2(clamped_prev_pos.right, clamped_prev_y),
        tl=Vec2(clamped_pos.left, clamped_y),
        tr=Vec2(clamped_pos.right, clamped_y),
    )
    return Layout.lane_transform.transform_quad(base)


def lane_hitbox(pos: LanePosition) -> Rect:
    return Rect(l=pos.left * Layout.scale, r=pos.right * Layout.scale, b=-1, t=1)


def preempt_time() -> float:
    speed = 10
    return 5 / speed


def note_y(scaled_time: float, target_scaled_time: float) -> float:
    return remap(
        target_scaled_time - preempt_time(),
        target_scaled_time,
        Layout.lane_height,
        0,
        scaled_time,
    )


def clamp_y_to_stage(y: float) -> float:
    return clamp(y, Layout.min_safe_y, Layout.lane_height)
