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

from mania.common.layout import preempt_time
from mania.common.options import Options


class TimescaleGroup(PlayArchetype):
    scaled_time: float = shared_memory()

    offset: float = entity_memory()

    @callback(order=-1)
    def preprocess(self):
        self.scaled_time = 0
        self.offset = 1

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
                change.end_time = 1e5
            change.end_scaled_time = scaled_time + change.scale * (change.end_time - change.start_time)
            scaled_time = change.end_scaled_time
            i += 1

    def update_sequential(self):
        if Options.disable_soflan:
            self.scaled_time = time()
            return
        if time() >= self.section().end_time:
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

    def time_to_scaled_time(self, real_time: float) -> float:
        if Options.disable_soflan:
            return real_time
        i = self.index + 1
        while True:
            section = TimescaleChange.at(i)
            if section.start_time <= real_time < section.end_time:
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

    def scaled_time_to_time(self, scaled_time: float) -> float:
        if Options.disable_soflan:
            return scaled_time
        i = self.index + 1
        while True:
            section = TimescaleChange.at(i)
            if (section.start_scaled_time <= scaled_time < section.end_scaled_time) or (
                section.start_scaled_time >= scaled_time > section.end_scaled_time
            ):
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
        scaled_time = self.time_to_scaled_time(target_time)
        start_scaled_time = max(scaled_time - preempt_time(), 0)
        start_time = self.scaled_time_to_time(start_scaled_time)
        return start_time, scaled_time


class TimescaleChange(PlayArchetype):
    beat: float = imported()
    scale: float = imported()

    start_scaled_time: float = shared_memory()
    end_scaled_time: float = shared_memory()
    end_time: float = shared_memory()

    @property
    def start_time(self) -> float:
        return beat_to_time(self.beat)

    def should_spawn(self) -> bool:
        return True

    def update_parallel(self):
        self.despawn = True
