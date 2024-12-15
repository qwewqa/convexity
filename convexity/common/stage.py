from math import ceil

from convexity.common.layout import LanePosition, Layer, Layout, lane_layout, line_layout
from convexity.common.options import Options
from convexity.common.skin import Skin


def draw_stage(pos: LanePosition):
    if Options.spread > 0 and not Options.laneless:
        return
    left_border_layout = lane_layout(LanePosition(pos.left - Layout.stage_border_width, pos.left))
    right_border_layout = lane_layout(LanePosition(pos.right, pos.right + Layout.stage_border_width))
    Skin.stage_left_border.draw(left_border_layout, z=Layer.STAGE)
    Skin.stage_right_border.draw(right_border_layout, z=Layer.STAGE)
    if Options.laneless:
        arc_quality = 5
        n_segments = 1 if not Options.arc else ceil(pos.width * arc_quality)
        start = pos.left
        segment_width = pos.width / n_segments
        for i in range(n_segments):
            segment_pos = LanePosition(start + i * segment_width, start + (i + 1) * segment_width)
            segment_layout = line_layout(segment_pos, 0)
            background_layout = lane_layout(segment_pos)
            Skin.judgment_line.draw(segment_layout, z=Layer.JUDGE_LINE)
            Skin.stage_middle.draw(background_layout, z=Layer.STAGE)
