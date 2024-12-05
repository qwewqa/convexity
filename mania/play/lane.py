from sonolus.script.archetype import PlayArchetype, callback, imported, shared_memory
from sonolus.script.quad import Quad

from mania.common.lane import draw_lane, play_lane_effects
from mania.common.layout import (
    LanePosition,
    lane_hitbox,
)
from mania.common.options import Options
from mania.play.input_manager import unused_touches


class Lane(PlayArchetype):
    pos: LanePosition = imported()

    hitbox: Quad = shared_memory()

    def spawn_order(self) -> float:
        return -1e8

    @callback(order=-1)
    def preprocess(self):
        if Options.mirror:
            self.pos @= self.pos.mirror()

    @callback(order=-1)
    def update_sequential(self):
        self.hitbox @= lane_hitbox(self.pos)

    def update_parallel(self):
        draw_lane(self.pos)

    @callback(order=1)
    def touch(self):
        for touch in unused_touches():
            if not touch.started:
                continue
            if self.hitbox.contains_point(touch.position):
                play_lane_effects(self.pos)
