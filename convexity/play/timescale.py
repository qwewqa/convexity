from __future__ import annotations

from sonolus.script.archetype import (
    PlayArchetype,
    callback,
    entity_memory,
    imported,
    shared_memory,
)
from sonolus.script.debug import error
from sonolus.script.interval import remap
from sonolus.script.runtime import time
from sonolus.script.timing import beat_to_time

from convexity.common.layout import preempt_time
from convexity.common.options import Options, SoflanMode


class TimescaleGroup(PlayArchetype):
    scaled_time: float = shared_memory()

    last_note_time: float = shared_memory()
    last_time_to_scaled_time_i: int = shared_memory()
    last_scaled_time_to_time_i: int = shared_memory()

    offset: float = entity_memory()

    @callback(order=-1)
    def preprocess(self):
        self.scaled_time = 0
        self.offset = 1
        self.last_note_time = 1e8

        i = self.index + 1
        scaled_time = 0
        while True:
            if not TimescaleChange.is_at(i):
                break
            change = TimescaleChange.at(i)
            change.start_scaled_time = scaled_time
            if TimescaleChange.is_at(i + 1):
                change.end_time = TimescaleChange.at(i + 1).start_time
            else:
                change.end_time = 1e8
            change.end_scaled_time = scaled_time + change.scale * (change.end_time - change.start_time)
            scaled_time = change.end_scaled_time
            i += 1

    def spawn_order(self) -> float:
        return -1e8

    @callback(order=-1)
    def update_sequential(self):
        match Options.soflan_mode:
            case SoflanMode.DISABLED:
                self.scaled_time = time()
            case _:
                while time() >= self.section().end_time:
                    self.offset += 1
                section = self.section()
                self.scaled_time = remap(
                    section.start_time,
                    section.end_time,
                    section.start_scaled_time,
                    section.end_scaled_time,
                    time(),
                )

    def section(self) -> TimescaleChange:
        return TimescaleChange.at(self.index + self.offset)

    def _time_to_scaled_time(self, real_time: float) -> float:
        match Options.soflan_mode:
            case SoflanMode.DISABLED:
                return real_time
            case _:
                i = self.last_time_to_scaled_time_i
                while True:
                    section = TimescaleChange.at(i)
                    if section.start_time <= real_time < section.end_time:
                        self.last_time_to_scaled_time_i = i
                        return remap(
                            section.start_time,
                            section.end_time,
                            section.start_scaled_time,
                            section.end_scaled_time,
                            real_time,
                        )
                    i += 1
                    if not TimescaleChange.is_at(i):
                        error()

    def _scaled_time_to_time(self, scaled_time: float) -> float:
        match Options.soflan_mode:
            case SoflanMode.DISABLED:
                return scaled_time
            case _:
                i = self.last_scaled_time_to_time_i
                while True:
                    section = TimescaleChange.at(i)
                    if (section.start_scaled_time <= scaled_time < section.end_scaled_time) or (
                        section.start_scaled_time >= scaled_time > section.end_scaled_time
                    ):
                        self.last_scaled_time_to_time_i = i
                        return remap(
                            section.start_scaled_time,
                            section.end_scaled_time,
                            section.start_time,
                            section.end_time,
                            scaled_time,
                        )
                    i += 1
                    if not TimescaleChange.is_at(i):
                        error()

    def get_note_times(self, target_time: float) -> tuple[float, float]:
        if target_time < self.last_note_time:
            # As long as the notes are increasing in time, we can start from the indexes we last visited
            self.last_time_to_scaled_time_i = self.index + 1
            self.last_scaled_time_to_time_i = self.index + 1
        self.last_note_time = target_time
        scaled_time = self._time_to_scaled_time(target_time)
        start_scaled_time = max(scaled_time - preempt_time(), -10)
        start_time = self._scaled_time_to_time(start_scaled_time)
        return start_time, scaled_time


class TimescaleChange(PlayArchetype):
    beat: float = imported()
    scale: float = imported()

    start_scaled_time: float = shared_memory()
    end_scaled_time: float = shared_memory()
    end_time: float = shared_memory()

    @property
    def start_time(self) -> float:
        return beat_to_time(self.beat) if self.beat > 0 else -10

    def should_spawn(self) -> bool:
        return True

    def update_parallel(self):
        self.despawn = True
