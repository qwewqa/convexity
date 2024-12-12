from sonolus.script.archetype import PlayArchetype, callback, entity_memory, imported
from sonolus.script.quad import Quad

from convexity.common.lane import draw_lane, play_lane_effects
from convexity.common.layout import (
    LanePosition,
    lane_hitbox,
    lane_to_pos,
)
from convexity.play.input_manager import unused_touches


class Lane(PlayArchetype):
    lane: int = imported()

    pos: LanePosition = entity_memory()
    hitbox: Quad = entity_memory()

    def spawn_order(self) -> float:
        return -1e8

    def preprocess(self):
        self.pos @= lane_to_pos(self.lane)
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
