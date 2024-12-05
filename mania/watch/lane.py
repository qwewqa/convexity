from sonolus.script.archetype import WatchArchetype, callback, imported

from mania.common.lane import draw_lane
from mania.common.layout import (
    LanePosition,
)
from mania.common.options import Options


class Lane(WatchArchetype):
    pos: LanePosition = imported()

    def spawn_time(self) -> float:
        return -1e8

    def despawn_time(self) -> float:
        return 1e8

    @callback(order=-1)
    def preprocess(self):
        if Options.mirror:
            self.pos @= self.pos.mirror()

    def update_parallel(self):
        draw_lane(self.pos)
