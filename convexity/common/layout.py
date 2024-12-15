from math import atan, cos, pi, sin, tan
from typing import Self

from sonolus.script.globals import level_data
from sonolus.script.interval import clamp, lerp, remap
from sonolus.script.quad import Quad, QuadLike, Rect
from sonolus.script.record import Record
from sonolus.script.transform import Transform2d
from sonolus.script.values import swap, zeros
from sonolus.script.vec import Vec2

from convexity.common.options import Options

EPSILON = 1e-3


class Layer:
    STAGE = 0
    LANE = 1
    JUDGE_LINE = 2
    SLOT = 3

    CONNECTOR = 1000

    NOTE = 2000
    ARROW = 2000 + 1e-4


@level_data
class Layout:
    vanishing_point: Vec2

    scale: float

    judge_line_y: float
    lane_length: float
    note_height: float
    sim_line_height: float

    stage_border_width: float

    approach_distance: float
    transform: Transform2d
    inverse_transform: Transform2d
    min_safe_y: float
    lane_max_screen_y: float
    approach_1_screen_y: float
    approach_0_screen_y: float

    reference_length: float


def init_layout():
    Layout.scale = 0.4 * Options.stage_size

    Layout.judge_line_y = lerp(-1, 1, Options.judge_line_position)
    Layout.lane_length = Options.lane_length * (1.05 if Options.extend_lanes else 1)
    Layout.note_height = Options.note_height
    Layout.sim_line_height = 0.3

    if Options.stage_tilt > 0:
        max_tilt_angle = atan(1.8)
        tilt_angle = remap(0, 1, pi / 2, max_tilt_angle, Options.stage_tilt)
        Layout.vanishing_point = Vec2(0, Layout.judge_line_y + Layout.scale * tan(tilt_angle))
    else:
        Layout.vanishing_point = Vec2(0, 1e6)

    Layout.stage_border_width = 0.125

    Layout.approach_distance = Options.linear_approach**3 * 999
    Layout.transform @= (
        Transform2d.new()
        .scale(Vec2(Layout.scale, Layout.scale))
        .perspective_y(Layout.judge_line_y, Layout.vanishing_point)
    )
    Layout.inverse_transform @= (
        Transform2d.new()
        .inverse_perspective_y(Layout.judge_line_y, Layout.vanishing_point)
        .scale(Vec2(1 / Layout.scale, 1 / Layout.scale))
    )
    Layout.lane_max_screen_y = Layout.transform.transform_vec(Vec2(0, Layout.lane_length)).y
    Layout.approach_1_screen_y = Layout.transform.transform_vec(
        Vec2(0, Layout.lane_length + Layout.approach_distance)
    ).y
    Layout.approach_0_screen_y = Layout.transform.transform_vec(Vec2(0, Layout.approach_distance)).y

    # Below this coordinate, points are "behind" the screen so they shouldn't be displayed.
    # We add half of the note height to make this the safe note center y-coordinate.
    Layout.min_safe_y = Layout.judge_line_y - Layout.vanishing_point.y + Layout.scale * Layout.note_height / 2 + EPSILON
    Layout.min_safe_y = max(Layout.min_safe_y, -2)  # Also don't go too far down

    Layout.reference_length = (transform_vec(Vec2(0.5, 0)) - transform_vec(Vec2(-0.5, 0))).magnitude


class LanePosition(Record):
    left: float
    right: float

    @property
    def mid(self) -> float:
        return (self.left + self.right) / 2

    @property
    def width(self) -> float:
        return self.right - self.left

    def scale_centered(self, factor: float) -> Self:
        mid = self.mid
        length = self.right - self.left
        half_length = length / 2
        return LanePosition(left=mid - half_length * factor, right=mid + half_length * factor)

    def __add__(self, other: Self) -> Self:
        return LanePosition(left=self.left + other.left, right=self.right + other.right)

    def __sub__(self, other: Self) -> Self:
        return LanePosition(left=self.left - other.left, right=self.right - other.right)

    def __mul__(self, other: float) -> Self:
        return LanePosition(left=self.left * other, right=self.right * other)

    def __truediv__(self, other: float) -> Self:
        return LanePosition(left=self.left / other, right=self.right / other)

    def mirror(self):
        return LanePosition(left=-self.right, right=-self.left)


def lane_to_pos(lane: float, width: float = 1) -> LanePosition:
    lane *= 1 + Options.spread
    half_width = width / 2
    return LanePosition(left=lane - half_width, right=lane + half_width)


def transform_quad(quad: QuadLike) -> Quad:
    return Quad(
        bl=transform_vec(quad.bl),
        br=transform_vec(quad.br),
        tl=transform_vec(quad.tl),
        tr=transform_vec(quad.tr),
    )


def transform_vec(vec: Vec2) -> Vec2:
    result = zeros(Vec2)
    if Options.arc and Options.stage_tilt > 0:
        vanishing_point_h = Layout.vanishing_point.y - Layout.judge_line_y
        angle = vec.x / vanishing_point_h * Layout.scale
        vec = Layout.transform.transform_vec(vec)
        h = Layout.vanishing_point.y - vec.y
        result @= Layout.vanishing_point + Vec2(h * sin(angle), -h * cos(angle))
    else:
        result @= Layout.transform.transform_vec(vec)
    return result


def lane_layout(pos: LanePosition) -> Quad:
    base = Rect(
        l=pos.left,
        r=pos.right,
        b=Layout.min_safe_y - Layout.note_height / 2,
        t=Layout.lane_length if not Options.extend_lanes else 999,
    )
    return transform_quad(base)


def lane_hitbox_layout(pos: LanePosition) -> Quad:
    hitbox = lane_layout(pos)
    # Extend it down
    hitbox.bl += (hitbox.bl - hitbox.tl) * 3
    hitbox.br += (hitbox.br - hitbox.tr) * 3
    return hitbox


def note_layout(pos: LanePosition, y: float) -> Quad:
    result = zeros(Quad)
    if Options.vertical_notes:
        scaled_pos = pos.scale_centered(Options.note_size)
        ml = transform_vec(Vec2(scaled_pos.left, y))
        mr = transform_vec(Vec2(scaled_pos.right, y))
        ort = (mr - ml).orthogonal()
        ort *= Layout.note_height / 2
        result @= Quad(
            bl=ml - ort,
            br=mr - ort,
            tl=ml + ort,
            tr=mr + ort,
        )
    else:
        base = Rect(
            l=pos.left,
            r=pos.right,
            b=y - Layout.note_height / 2,
            t=y + Layout.note_height / 2,
        ).scale_centered(Vec2(Options.note_size, Options.note_size))
        result @= transform_quad(base)
    return result


def line_layout(pos: LanePosition, y: float) -> Quad:
    base = Rect(
        l=pos.left,
        r=pos.right,
        b=y - Layout.note_height / 2 / 5,
        t=y + Layout.note_height / 2 / 5,
    )
    return transform_quad(base)


def note_particle_layout(pos: LanePosition) -> Quad:
    bl = transform_vec(Vec2(pos.left, 0))
    br = transform_vec(Vec2(pos.right, 0))
    h = (br - bl).rotate(pi / 2) * Options.note_effect_size
    return Quad(
        bl=bl,
        br=br,
        tl=bl + h,
        tr=br + h,
    )


def connector_layout(
    pos: LanePosition,
    y: float,
    prev_pos: LanePosition,
    prev_y: float,
) -> Quad:
    base = Quad(
        bl=Vec2(prev_pos.left, prev_y),
        br=Vec2(prev_pos.right, prev_y),
        tl=Vec2(pos.left, y),
        tr=Vec2(pos.right, y),
    )
    return transform_quad(base)


def sim_line_layout(
    pos: LanePosition,
    y: float,
    sim_pos: LanePosition,
    sim_y: float,
):
    mid_l = Vec2(pos.mid, y)
    mid_r = Vec2(sim_pos.mid, sim_y)
    if mid_l.x > mid_r.x:
        swap(mid_l, mid_r)
    ort = (mid_r - mid_l).orthogonal().normalize()
    ort *= Layout.sim_line_height / 2
    base = Quad(
        bl=mid_l - ort,
        br=mid_r - ort,
        tl=mid_l + ort,
        tr=mid_r + ort,
    )
    return transform_quad(base)


def segments_intersect(a1, a2, b1, b2):
    def orientation(p, q, r):
        return (r.y - p.y) * (q.x - p.x) > (q.y - p.y) * (r.x - p.x)

    o1 = orientation(a1, b1, b2)
    o2 = orientation(a2, b1, b2)
    o3 = orientation(a1, a2, b1)
    o4 = orientation(a1, a2, b2)

    return o1 != o2 and o3 != o4


def lane_hitbox_pos(lane: float, leniency: float = 1, direction: float = 0) -> LanePosition:
    return lane_to_pos(lane + direction / 2, (leniency + abs(direction)) * (1 + Options.spread))


def lane_hitbox(pos: LanePosition) -> Quad:
    result = zeros(Quad)
    if Options.angled_hitboxes or Options.arc:
        result @= lane_hitbox_layout(pos)
    else:
        result @= Rect(l=pos.left * Layout.scale, r=pos.right * Layout.scale, b=-1, t=1).as_quad()
    return result


def preempt_time() -> float:
    return 5 / Options.note_speed * (1.05 if Options.extend_lanes else 1)


def note_y(scaled_time: float, target_scaled_time: float) -> float:
    if Layout.approach_distance:
        approach_y = (
            remap(
                target_scaled_time - preempt_time(),
                target_scaled_time,
                Layout.lane_length,
                0,
                scaled_time,
            )
            + Layout.approach_distance
        )
        screen_y = remap(
            Layout.approach_0_screen_y,
            Layout.approach_1_screen_y,
            Layout.judge_line_y,
            Layout.lane_max_screen_y,
            Layout.transform.transform_vec(Vec2(0, approach_y)).y,
        )
        screen_y = min(screen_y, Layout.vanishing_point.y - 1e-2)
        return Layout.inverse_transform.transform_vec(Vec2(0, screen_y)).y
    return remap(
        target_scaled_time - preempt_time(),
        target_scaled_time,
        Layout.lane_length,
        0,
        scaled_time,
    )


def clamp_y_to_stage(y: float) -> float:
    return clamp(y, Layout.min_safe_y, Layout.lane_length)
