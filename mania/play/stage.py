from sonolus.script.archetype import PlayArchetype, imported

from mania.common.layout import (
    LanePosition,
)
from mania.common.stage import draw_stage
from mania.play.init import Init


class Stage(PlayArchetype):
    pos: LanePosition = imported()

    def spawn_order(self) -> float:
        return -1e8

    def should_spawn(self) -> bool:
        return Init.at(0).is_despawned

    def update_parallel(self):
        draw_stage(self.pos)
