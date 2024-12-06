from sonolus.script.archetype import PlayArchetype, callback, entity_data, imported
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

    hitbox: Quad = entity_data()

    def spawn_order(self) -> float:
        return -1e8

    def preprocess(self):
        if Options.mirror:
            self.pos @= self.pos.mirror()
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
