from sonolus.script.archetype import EntityRef, PlayArchetype, imported

from mania.play.timescale_group import TimescaleGroup


class TimescaleChange(PlayArchetype):
    group: EntityRef[TimescaleGroup] = imported()
    time: float = imported()
    scale: float = imported()

    def spawn_order(self) -> float:
        return self.time

    def update_sequential(self):
        group = self.group.get()
        if group.group_start_time > self.time:
            self.despawn = True
            return
        group.group_start_time = max(self.time, group.group_start_time)
