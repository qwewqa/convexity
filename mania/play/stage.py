
from sonolus.script.archetype import PlayArchetype, imported

from mania.common.layout import (
    LanePosition,
    Layer,
    Layout,
    lane_layout,
)
from mania.common.skin import Skin
from mania.play.init import Init


class Stage(PlayArchetype):
    pos: LanePosition = imported()

    def spawn_order(self) -> int:
        return -1

    def should_spawn(self) -> bool:
        return Init.at(0).is_despawned

    def update_parallel(self):
        left_border_layout = lane_layout(
            LanePosition(self.pos.left - Layout.stage_border_width, self.pos.left)
        )
        right_border_layout = lane_layout(
            LanePosition(self.pos.right, self.pos.right + Layout.stage_border_width)
        )
        Skin.stage_left_border.draw(left_border_layout, z=Layer.STAGE)
        Skin.stage_right_border.draw(right_border_layout, z=Layer.STAGE)
