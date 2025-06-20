from math import asin, atan, atan2, cos, pi, sin, tan
from typing import Self

from sonolus.script.easing import ease_out_cubic, ease_out_sine
from sonolus.script.globals import level_data, level_memory
from sonolus.script.interval import clamp, lerp, remap, unlerp
from sonolus.script.quad import Quad, QuadLike, Rect
from sonolus.script.record import Record
from sonolus.script.runtime import delta_time, is_preprocessing, is_preview, is_skip, time
from sonolus.script.transform import Transform2d
from sonolus.script.values import swap, zeros
from sonolus.script.vec import Vec2

from convexity.common.options import LaneMode, Options, ScrollMode

EPSILON = 1e-3


class Layer:
    STAGE = 0
    LANE = 1
    JUDGE_LINE = 2
    SLOT = 3

    CONNECTOR = 1000

    COVER = 2000
    MEASURE_LINE = 2001
    SIM_LINE = 2002
    TIME_LINE = 2003
    BPM_CHANGE_LINE = 2004

    NOTE_HEAD = 3000
    NOTE = 3001
    ARROW = 3001 + 0.01

    TOUCH_LINE = 4000


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
    Layout.note_height = Options.note_height * (Options.lane_width if not is_preview() else 1)
    Layout.sim_line_height = 1.0

    if Options.stage_tilt > 0:
        max_tilt_angle = atan(1.8)
        tilt_angle = remap(0, 1, pi / 2, max_tilt_angle, Options.stage_tilt)
        Layout.vanishing_point = Vec2(0, Layout.judge_line_y + Layout.scale * tan(tilt_angle))
    else:
        Layout.vanishing_point = Vec2(0, 1e6)

    Layout.stage_border_width = 0.125

    # This empirically works well enough. There isn't a particular reason for this formula.
    Layout.approach_distance = 99 ** asin(Options.linear_approach) - 1
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
    Layout.min_safe_y = max(Layout.min_safe_y, -4)  # Also don't go too far down

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
    lane *= 1 + (Options.lane_spacing if not is_preview() else 0)
    lane *= Options.lane_width if not is_preview() else 1
    half_width = width / 2
    half_width *= Options.lane_width if not is_preview() else 1
    return LanePosition(left=lane - half_width, right=lane + half_width)


def adjusted_lane_to_pos(lane: float, scaled_time: float, target_scaled_time: float, width: float = 1):
    progress = unlerp(
        target_scaled_time - preempt_time(),
        target_scaled_time,
        scaled_time,
    )
    result = zeros(LanePosition)
    match Options.lane_mode:
        case LaneMode.SPREAD:
            alpha = 0.8
            adjusted_progress = 1 - alpha + alpha * ease_out_cubic(progress)
            result @= lane_to_pos(lane * adjusted_progress, width)
        case LaneMode.WAVE:
            intensity = 1
            time_period = 20
            progress_cycles = 0.5
            adjusted_lane = lane + (1 - ease_out_sine(progress)) * intensity * sin(
                target_scaled_time * 2 * pi / time_period + progress * 2 * pi * progress_cycles
            )
            result @= lane_to_pos(adjusted_lane, width)
        case LaneMode.CROSSOVER:
            adjusted_lane = lane * 2 * (progress - 0.5)
            result @= lane_to_pos(adjusted_lane, width)
        case _:
            result @= lane_to_pos(lane, width)
    return result


def touch_pos_to_lane(pos: Vec2) -> float:
    inverted_pos = zeros(Vec2)
    if not Options.angled_hitboxes and not Options.arc:
        inverted_pos @= inverse_transform_vec(Vec2(pos.x, Layout.judge_line_y))
    else:
        inverted_pos @= inverse_transform_vec(pos)
    lane = inverted_pos.x
    lane /= Options.lane_width
    lane /= 1 + Options.lane_spacing
    return lane


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


def inverse_transform_vec(vec: Vec2) -> Vec2:
    result = zeros(Vec2)
    if Options.arc and Options.stage_tilt > 0:
        vanishing_point_h = Layout.vanishing_point.y - Layout.judge_line_y
        relative_vec = vec - Layout.vanishing_point

        h = relative_vec.magnitude
        if h < EPSILON:
            result @= Layout.vanishing_point + Vec2(0, -EPSILON)
        else:
            angle = atan2(relative_vec.x, -relative_vec.y)

            original_x = angle * vanishing_point_h / Layout.scale
            original_y = Layout.inverse_transform.transform_vec(Vec2(0, Layout.vanishing_point.y - h)).y
            result @= Vec2(original_x, original_y)
    else:
        result @= Layout.inverse_transform.transform_vec(vec)
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
        b=y - Layout.note_height / 2,
        t=y + Layout.note_height / 2,
    )
    return transform_quad(base)


def note_particle_linear_layout(pos: LanePosition) -> Quad:
    result = zeros(Quad)
    if Options.note_effect_linear_enabled:
        bl = transform_vec(Vec2(pos.left, 0))
        br = transform_vec(Vec2(pos.right, 0))
        h = (br - bl).rotate(pi / 2) * Options.note_effect_size
        result @= Quad(
            bl=bl,
            br=br,
            tl=bl + h,
            tr=br + h,
        )
    else:
        result @= Rect(-9, 9, -9, 9).as_quad()
    return result


def note_particle_circular_layout(pos: LanePosition) -> Quad:
    result = zeros(Quad)
    if Options.note_effect_circular_enabled:
        scale = 1.8
        base_layout = note_layout(pos, 0)
        ml = (base_layout.bl + base_layout.tl) / 2
        mr = (base_layout.br + base_layout.tr) / 2
        c = (ml + mr) / 2
        ml @= c + (ml - c) * scale
        mr @= c + (mr - c) * scale
        ort = (mr - ml).orthogonal() / 2
        result @= Quad(
            bl=ml - ort,
            br=mr - ort,
            tl=ml + ort,
            tr=mr + ort,
        )
    else:
        result @= Rect(-9, 9, -9, 9).as_quad()
    return result


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
    return lane_to_pos(lane + direction / 2, (leniency + abs(direction)) * (1 + Options.lane_spacing))


def lane_hitbox(pos: LanePosition) -> Quad:
    result = zeros(Quad)
    if Options.angled_hitboxes or Options.arc:
        result @= lane_hitbox_layout(pos)
    else:
        result @= Rect(l=pos.left * Layout.scale, r=pos.right * Layout.scale, b=-1, t=1).as_quad()
    return result


def preempt_time() -> float:
    base = 5 / Options.note_speed * (1.05 if Options.extend_lanes else 1)
    match Options.scroll_mode:
        case ScrollMode.CHAOS:
            period = 6
            lo = 1
            hi = 4
            if is_preprocessing():
                return hi * base
            else:
                return 1 / lerp(1 / lo, 1 / hi, (sin(time() * 2 * pi / period) + 1) / 2) * base
        case _:
            return base


@level_memory
class LayoutMemory:
    backspin_level: float
    backspin_reserve: float


def update_backspin():
    drain_rate = 15
    apply_rate = 15
    if is_skip():
        LayoutMemory.backspin_reserve = 0
        LayoutMemory.backspin_level = 0
    backspin_level = LayoutMemory.backspin_level
    backspin_reserve = min(1.0, LayoutMemory.backspin_reserve)
    apply = min(backspin_reserve, delta_time() * apply_rate)
    backspin_reserve -= apply
    backspin_level += apply
    if apply == 0:
        backspin_level = max(0.0, backspin_level - delta_time() * drain_rate)
    LayoutMemory.backspin_level = backspin_level
    LayoutMemory.backspin_reserve = backspin_reserve


def add_backspin():
    LayoutMemory.backspin_reserve += 1


def note_y(scaled_time: float, target_scaled_time: float) -> float:
    progress = unlerp(
        target_scaled_time - preempt_time(),
        target_scaled_time,
        scaled_time,
    )
    progress = 1 - (1 - progress) * (1 + min(1.0, LayoutMemory.backspin_level) * Options.note_speed * 0.2 / 10)
    if Layout.approach_distance:
        approach_y = (
            lerp(
                Layout.lane_length,
                0,
                progress,
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
        return min(
            Layout.inverse_transform.transform_vec(Vec2(0, screen_y)).y,
            max(
                lerp(
                    Layout.lane_length,
                    0,
                    progress,
                ),
                0,
            ),
        )
    return lerp(
        Layout.lane_length,
        0,
        progress,
    )


def clamp_y_to_stage(y: float) -> float:
    return clamp(y, Layout.min_safe_y, Layout.lane_length)
