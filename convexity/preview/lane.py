from sonolus.script.archetype import PreviewArchetype, entity_data, imported

from convexity.common.layout import LanePosition, Layer, lane_to_pos
from convexity.common.options import Options
from convexity.common.skin import Skin
from convexity.preview.layout import PreviewData, PreviewLayout, lane_layout


class Lane(PreviewArchetype):
    lane: float = imported()

    pos: LanePosition = entity_data()

    def preprocess(self):
        if Options.mirror:
            self.lane *= -1

        PreviewData.highest_lane = max(PreviewData.highest_lane, abs(self.lane))
        self.pos @= lane_to_pos(self.lane)

    def render(self):
        for col in range(PreviewLayout.column_count):
            layout = lane_layout(self.pos, col)
            Skin.lane.draw(layout, z=Layer.LANE)
