from sonolus.script.archetype import WatchArchetype, imported

from mania.common.layout import (
    LanePosition,
)
from mania.common.stage import draw_stage


class Stage(WatchArchetype):
    pos: LanePosition = imported()

    def spawn_time(self) -> float:
        return -1e8

    def despawn_time(self) -> bool:
        return 1e8

    def update_parallel(self):
        draw_stage(self.pos)
