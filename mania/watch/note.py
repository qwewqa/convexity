from __future__ import annotations

from sonolus.script.archetype import (
    EntityRef,
    StandardImport,
    WatchArchetype,
    entity_data,
    entity_memory,
    imported,
    shared_memory,
)
from sonolus.script.bucket import Bucket, Judgment, JudgmentWindow
from sonolus.script.interval import lerp, unlerp
from sonolus.script.particle import Particle
from sonolus.script.runtime import is_replay, time
from sonolus.script.sprite import Sprite
from sonolus.script.timing import beat_to_time

from mania.common.layout import (
    note_y,
)
from mania.common.note import (
    HoldHandle,
    NoteVariant,
    draw_note_body,
    draw_note_connector,
    note_body_sprite,
    note_bucket,
    note_connector_sprite,
    note_head_sprite,
    note_hold_particle,
    note_particle,
    note_window,
    play_watch_hit_effects,
    schedule_watch_hit_effects,
)
from mania.watch.lane import Lane
from mania.watch.timescale import TimescaleGroup


class Note(WatchArchetype):
    is_scored = True

    variant: NoteVariant = imported()
    beat: float = imported()
    lane_ref: EntityRef[Lane] = imported()
    timescale_group_ref: EntityRef[TimescaleGroup] = imported()
    prev_note_ref: EntityRef[Note] = imported()

    touch_id: int = shared_memory()
    y: float = shared_memory()

    target_time: float = entity_data()
    window: JudgmentWindow = entity_data()
    bucket: Bucket = entity_data()
    body_sprite: Sprite = entity_data()
    head_sprite: Sprite = entity_data()
    connector_sprite: Sprite = entity_data()
    particle: Particle = entity_data()
    hold_particle: Particle = entity_data()
    has_prev: bool = entity_data()
    start_time: float = entity_data()
    target_scaled_time: float = entity_data()

    started: bool = entity_memory()
    hold_handle: HoldHandle = entity_memory()

    judgment: StandardImport.JUDGMENT
    accuracy: StandardImport.ACCURACY
    finish_time: float = imported()

    def preprocess(self):
        self.target_time = beat_to_time(self.beat)
        self.window @= note_window(self.variant)
        self.bucket @= note_bucket(self.variant)
        self.body_sprite @= note_body_sprite(self.variant)
        self.head_sprite @= note_head_sprite(self.variant)
        self.connector_sprite @= note_connector_sprite(self.variant)
        self.particle @= note_particle(self.variant)
        self.hold_particle @= note_hold_particle(self.variant)
        self.has_prev = self.prev_note_ref.index > 0

        self.start_time, self.target_scaled_time = self.timescale_group.get_note_times(self.target_time)

        self.result.target_time = self.target_time

        if is_replay():
            self.result.bucket @= self.bucket
            self.result.bucket_value = self.accuracy * 1000
            schedule_watch_hit_effects(self.finish_time, self.judgment)
        else:
            self.result.bucket @= self.bucket
            self.result.bucket_value = 0
            schedule_watch_hit_effects(self.target_time, Judgment.PERFECT)

    def spawn_time(self) -> float:
        return min(self.start_time, self.prev_start_time)

    def despawn_time(self) -> float:
        if is_replay():
            return self.finish_time
        else:
            return self.target_time

    def update_sequential(self):
        self.y = note_y(self.timescale_group.scaled_time, self.target_scaled_time)

    def update_parallel(self):
        self.draw_body()
        self.draw_connector()

    def draw_body(self):
        draw_note_body(
            sprite=self.body_sprite,
            pos=self.lane.pos,
            y=self.y,
        )

    def draw_connector(self):
        if not self.has_prev:
            return
        prev = self.prev
        if time() < prev.despawn_time():
            draw_note_connector(
                sprite=self.connector_sprite,
                pos=self.lane.pos,
                y=self.y,
                prev_pos=prev.lane.pos,
                prev_y=prev.y,
            )
        elif time() < self.target_time:
            prev_target_time = prev.target_time
            target_time = self.target_time
            progress = unlerp(prev_target_time, target_time, time())
            prev_pos = lerp(prev.lane.pos, self.lane.pos, progress)
            draw_note_connector(
                sprite=self.connector_sprite,
                pos=self.lane.pos,
                y=self.y,
                prev_pos=prev_pos,
                prev_y=0,
            )
            draw_note_body(
                sprite=self.head_sprite,
                pos=prev_pos,
                y=0,
            )
            self.hold_handle.update(
                particle=self.hold_particle,
                pos=prev_pos,
            )

    def terminate(self):
        self.hold_handle.destroy()
        if not is_replay() or self.judgment != Judgment.MISS:
            play_watch_hit_effects(
                note_particle=self.particle,
                pos=self.lane.pos,
            )

    @property
    def lane(self) -> Lane:
        return self.lane_ref.get()

    @property
    def timescale_group(self) -> TimescaleGroup:
        return self.timescale_group_ref.get()

    @property
    def prev(self) -> Note:
        return self.prev_note_ref.get()

    @property
    def prev_start_time(self) -> float:
        if not self.has_prev:
            return 1e8
        return self.prev_note_ref.get().start_time


class UnscoredNote(Note):
    is_scored = False
