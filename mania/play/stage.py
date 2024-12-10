from sonolus.script.archetype import PlayArchetype, entity_memory, imported

from mania.common.layout import (
    LanePosition,
    lane_to_pos,
)
from mania.common.options import Options
from mania.common.stage import draw_stage


class Stage(PlayArchetype):
    lane: float = imported()
    width: float = imported()

    pos: LanePosition = entity_memory()

    def spawn_order(self) -> float:
        return -1e8

    def preprocess(self):
        self.pos @= lane_to_pos(self.lane, self.width * (1 + Options.spread))

    def update_parallel(self):
        draw_stage(self.pos)
