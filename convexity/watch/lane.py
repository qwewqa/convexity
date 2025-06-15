from sonolus.script.archetype import WatchArchetype, entity_memory, imported
from sonolus.script.runtime import delta_time, time

from convexity.common.lane import draw_lane, play_lane_particle
from convexity.common.layout import (
    LanePosition,
    lane_to_pos,
)
from convexity.common.options import Options
from convexity.common.streams import Streams


class Lane(WatchArchetype):
    lane: float = imported()

    pos: LanePosition = entity_memory()

    def spawn_time(self) -> float:
        return -1e8

    def despawn_time(self) -> float:
        return 1e8

    def preprocess(self):
        if Options.mirror:
            self.lane *= -1

        self.pos @= lane_to_pos(self.lane)

    def update_parallel(self):
        draw_lane(self.pos)
        start_key = Streams.empty_touch_lanes.next_key(time() - delta_time())
        for effect_time, lanes in Streams.empty_touch_lanes.iter_items_from(start_key):
            if effect_time > time():
                break
            if self.lane in lanes:
                play_lane_particle(self.pos)
                break
