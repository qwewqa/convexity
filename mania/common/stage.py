from mania.common.layout import LanePosition, Layer, Layout, lane_layout
from mania.common.skin import Skin


def draw_stage(pos: LanePosition):
    left_border_layout = lane_layout(LanePosition(pos.left - Layout.stage_border_width, pos.left))
    right_border_layout = lane_layout(LanePosition(pos.right, pos.right + Layout.stage_border_width))
    Skin.stage_left_border.draw(left_border_layout, z=Layer.STAGE)
    Skin.stage_right_border.draw(right_border_layout, z=Layer.STAGE)
