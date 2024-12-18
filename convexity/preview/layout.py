from math import ceil, floor, pi, trunc
from typing import Literal

from sonolus.script.globals import level_data
from sonolus.script.interval import lerp
from sonolus.script.printing import PrintColor, PrintFormat, print_number
from sonolus.script.quad import Quad, Rect
from sonolus.script.runtime import HorizontalAlign, ScrollDirection, canvas, screen
from sonolus.script.vec import Vec2

from convexity.common.layout import LanePosition
from convexity.common.options import Options

COLUMN_SECS = 2
MARGIN_Y = 0.1
MARGIN_X = 0.25
TEXT_MARGIN_X = 0.015
TEXT_MARGIN_Y = 0
TEXT_HEIGHT = 0.12
LANE_WIDTH = 0.072
LINE_HEIGHT = 0.05
LINE_ALPHA = 0.8
COVER_ALPHA = 1.0
Y_B = -1 + MARGIN_Y
Y_T = 1 - MARGIN_Y


@level_data
class PreviewData:
    highest_lane: float
    last_time: float
    last_beat: float


@level_data
class PreviewLayout:
    lane_count: int
    column_count: int
    column_width: float


def init_preview_layout():
    PreviewLayout.lane_count = ceil(PreviewData.highest_lane * 2)
    PreviewLayout.column_count = floor(PreviewData.last_time / COLUMN_SECS) + 1
    PreviewLayout.column_width = 2 * MARGIN_X + LANE_WIDTH * PreviewLayout.lane_count

    canvas().update(
        scroll_direction=ScrollDirection.LEFT_TO_RIGHT,
        size=PreviewLayout.column_width * PreviewLayout.column_count,
    )


def time_to_col(time: float) -> int:
    return trunc(time / COLUMN_SECS)


def time_to_y(time: float) -> float:
    return lerp(Y_B, Y_T, time % COLUMN_SECS / COLUMN_SECS)


def lane_to_x(lane: float, col: int) -> float:
    return (col + 0.5) * PreviewLayout.column_width + lane * LANE_WIDTH - screen().w / 2


def lane_layout(pos: LanePosition, col: int) -> Rect:
    return Rect(
        l=lane_to_x(pos.left, col),
        r=lane_to_x(pos.right, col),
        t=1,
        b=-1,
    )


def note_layout(pos: LanePosition, time: float) -> Rect:
    col = time_to_col(time)
    y = time_to_y(time)
    return Rect(
        l=lane_to_x(pos.left, col),
        r=lane_to_x(pos.right, col),
        t=y + LANE_WIDTH / 2,
        b=y - LANE_WIDTH / 2,
    ).scale_centered(Vec2(1, Options.note_height))


def arrow_layout(pos: LanePosition, time: float, direction: float = 0, y_offset: float = 0) -> Quad:
    col = time_to_col(time)
    y = time_to_y(time) + y_offset * LANE_WIDTH * Options.note_height
    angle = 0
    if direction < 0:
        angle = pi / 2
    elif direction > 0:
        angle = -pi / 2
    return (
        Rect(
            l=lane_to_x(pos.left, col),
            r=lane_to_x(pos.right, col),
            t=y + LANE_WIDTH / 2,
            b=y - LANE_WIDTH / 2,
        )
        .as_quad()
        .rotate_centered(angle)
    )


def connector_layout(
    pos: LanePosition,
    time: float,
    prev_pos: LanePosition,
    prev_time: float,
    col: int,
) -> Quad:
    col_time = col * COLUMN_SECS
    scaled_pos = LanePosition(lane_to_x(pos.left, col), lane_to_x(pos.right, col))
    scaled_prev_pos = LanePosition(lane_to_x(prev_pos.left, col), lane_to_x(prev_pos.right, col))
    y = lerp(
        Y_B,
        Y_T,
        (time - col_time) / COLUMN_SECS,
    )
    prev_y = lerp(
        Y_B,
        Y_T,
        (prev_time - col_time) / COLUMN_SECS,
    )
    return Quad(
        bl=Vec2(scaled_prev_pos.left, prev_y),
        br=Vec2(scaled_prev_pos.right, prev_y),
        tr=Vec2(scaled_pos.right, y),
        tl=Vec2(scaled_pos.left, y),
    )


def sim_line_layout(
    pos: LanePosition,
    sim_pos: LanePosition,
    time: float,
) -> Quad:
    col = time_to_col(time)
    l = lane_to_x(pos.mid, col)
    r = lane_to_x(sim_pos.mid, col)
    if l > r:
        l, r = r, l
    y = time_to_y(time)
    return Quad(
        bl=Vec2(l, y - LANE_WIDTH / 2 / 4),
        br=Vec2(r, y - LANE_WIDTH / 2 / 4),
        tr=Vec2(r, y + LANE_WIDTH / 2 / 4),
        tl=Vec2(l, y + LANE_WIDTH / 2 / 4),
    )


def inner_line_layout(
    time: float,
) -> Quad:
    col = time_to_col(time)
    l = lane_to_x(-PreviewLayout.lane_count / 2, col)
    r = lane_to_x(PreviewLayout.lane_count / 2, col)
    y = time_to_y(time)
    return Quad(
        bl=Vec2(l, y - LANE_WIDTH / 2 * LINE_HEIGHT),
        br=Vec2(r, y - LANE_WIDTH / 2 * LINE_HEIGHT),
        tr=Vec2(r, y + LANE_WIDTH / 2 * LINE_HEIGHT),
        tl=Vec2(l, y + LANE_WIDTH / 2 * LINE_HEIGHT),
    )


def left_right_line_layout(
    time: float,
) -> Quad:
    col = time_to_col(time)
    l = lane_to_x(-PreviewLayout.lane_count / 2 - 3, col)
    r = lane_to_x(PreviewLayout.lane_count / 2 + 3, col)
    y = time_to_y(time)
    return Quad(
        bl=Vec2(l, y - LANE_WIDTH / 2 * LINE_HEIGHT),
        br=Vec2(r, y - LANE_WIDTH / 2 * LINE_HEIGHT),
        tr=Vec2(r, y + LANE_WIDTH / 2 * LINE_HEIGHT),
        tl=Vec2(l, y + LANE_WIDTH / 2 * LINE_HEIGHT),
    )


def left_line_layout(
    time: float,
) -> Quad:
    col = time_to_col(time)
    l = lane_to_x(-PreviewLayout.lane_count / 2 - 3, col)
    r = lane_to_x(-PreviewLayout.lane_count / 2, col)
    y = time_to_y(time)
    return Quad(
        bl=Vec2(l, y - LANE_WIDTH / 2 * LINE_HEIGHT),
        br=Vec2(r, y - LANE_WIDTH / 2 * LINE_HEIGHT),
        tr=Vec2(r, y + LANE_WIDTH / 2 * LINE_HEIGHT),
        tl=Vec2(l, y + LANE_WIDTH / 2 * LINE_HEIGHT),
    )


def print_at_time(
    value: float,
    time: float,
    *,
    fmt: PrintFormat,
    decimal_places: int = -1,
    color: PrintColor,
    side: Literal["left", "right"],
):
    print_number(
        value=value,
        fmt=fmt,
        decimal_places=decimal_places,
        anchor=Vec2(
            lane_to_x(
                -PreviewLayout.lane_count / 2 if side == "left" else PreviewLayout.lane_count / 2,
                time_to_col(time),
            )
            + (-TEXT_MARGIN_X if side == "left" else TEXT_MARGIN_X),
            time_to_y(time) + TEXT_MARGIN_Y,
        ),
        pivot=Vec2(1 if side == "left" else 0, 0),
        dimensions=Vec2(MARGIN_X - 2 * TEXT_MARGIN_X, TEXT_HEIGHT),
        color=color,
        horizontal_align=HorizontalAlign.RIGHT if side == "left" else HorizontalAlign.LEFT,
        background=False,
    )
