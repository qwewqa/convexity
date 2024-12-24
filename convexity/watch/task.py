from sonolus.script.archetype import WatchArchetype, callback, entity_memory

from convexity.common.layout import add_backspin


class BackspinTask(WatchArchetype):
    time: float = entity_memory()
    done: bool = entity_memory()

    def spawn_time(self) -> float:
        return self.time

    def despawn_time(self) -> float:
        return self.time + 0.1

    def initialize(self):
        self.done = False

    @callback(order=-1)
    def update_sequential(self):
        if self.done:
            return
        self.done = True
        add_backspin()
