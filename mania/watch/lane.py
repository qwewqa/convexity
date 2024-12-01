from sonolus.script.archetype import WatchArchetype, callback, imported

from mania.common.lane import draw_lane, play_lane_effects
from mania.common.layout import (
    LanePosition,
    lane_hitbox,
)
from mania.common.options import Options
from mania.play.input_manager import unused_touches


class Lane(WatchArchetype):
    pos: LanePosition = imported()

    def spawn_time(self) -> float:
        return -1e8

    def despawn_time(self) -> float:
        return 1e8

    @callback(order=-2)
    def preprocess(self):
        if Options.mirror:
            self.pos @= self.pos.mirror()

    def update_parallel(self):
        draw_lane(self.pos)

    @callback(order=1)
    def touch(self):
        for touch in unused_touches():
            if not touch.started:
                continue
            if self.hitbox.contains_point(touch.position):
                play_lane_effects(self.pos)

    @property
    def hitbox(self):
        return lane_hitbox(self.pos)
