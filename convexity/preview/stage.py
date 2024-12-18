from sonolus.script.archetype import PreviewArchetype, imported

from convexity.common.layout import LanePosition, Layer, Layout, lane_to_pos
from convexity.common.options import Options
from convexity.common.skin import Skin
from convexity.preview.layout import PreviewData, PreviewLayout, lane_layout


class Stage(PreviewArchetype):
    lane: float = imported()
    width: float = imported()

    def preprocess(self):
        if Options.mirror:
            self.lane *= -1

        PreviewData.highest_lane = max(PreviewData.highest_lane, abs(self.lane) + self.width / 2)

    def render(self):
        pos = lane_to_pos(self.lane, self.width)
        for col in range(PreviewLayout.column_count):
            left_border_layout = lane_layout(LanePosition(pos.left - Layout.stage_border_width, pos.left), col)
            right_border_layout = lane_layout(LanePosition(pos.right, pos.right + Layout.stage_border_width), col)
            Skin.stage_left_border.draw(left_border_layout, z=Layer.STAGE)
            Skin.stage_right_border.draw(right_border_layout, z=Layer.STAGE)
