from __future__ import annotations

from enum import IntEnum

from sonolus.script.archetype import (
    EntityRef,
    StandardImport,
    WatchArchetype,
    entity_memory,
    imported,
    shared_memory,
)
from sonolus.script.bucket import Judgment, JudgmentWindow
from sonolus.script.interval import lerp, unlerp
from sonolus.script.runtime import is_replay, time
from sonolus.script.timing import beat_to_time
from sonolus.script.values import copy

from mania.common.buckets import Buckets, note_judgment_window
from mania.common.layout import (
    note_y,
)
from mania.common.note import (
    HoldHandle,
    draw_connector,
    draw_note,
    play_watch_hit_effects,
    schedule_watch_hit_effects,
)
from mania.common.particle import Particles
from mania.common.skin import Skin
from mania.watch.lane import Lane
from mania.watch.timescale import TimescaleGroup


class NoteVariant(IntEnum):
    SINGLE = 0
    HOLD_START = 1
    HOLD_END = 2


class Note(WatchArchetype):
    is_scored = True

    variant: NoteVariant = imported()
    beat: float = imported()
    lane_ref: EntityRef[Lane] = imported()
    timescale_group_ref: EntityRef[TimescaleGroup] = imported()
    prev_note_ref: EntityRef[Note] = imported()

    touch_id: int = shared_memory()
    start_time: float = shared_memory()
    target_scaled_time: float = shared_memory()

    hold_handle: HoldHandle = entity_memory()

    judgment: StandardImport.JUDGMENT
    accuracy: StandardImport.ACCURACY
    finish_time: float = imported()

    def preprocess(self):
        self.result.target_time = self.target_time
        self.start_time, self.target_scaled_time = self.timescale_group.get_note_times(self.target_time)

        if is_replay():
            self.result.bucket @= self.bucket
            self.result.bucket_value = self.accuracy * 1000
            schedule_watch_hit_effects(self.finish_time, self.judgment)
        else:
            self.result.bucket @= Buckets.tap_note
            self.result.bucket_value = 0
            schedule_watch_hit_effects(self.target_time, Judgment.PERFECT)

    def spawn_time(self) -> float:
        return min(self.start_time, self.prev_start_time)

    def despawn_time(self) -> float:
        if is_replay():
            return self.finish_time
        else:
            return self.target_time

    def update_parallel(self):
        self.draw_body()
        self.draw_connector()

    def draw_body(self):
        draw_note(
            sprite=self.body_sprite,
            pos=self.lane.pos,
            y=self.y,
        )

    def draw_connector(self):
        if not self.prev_note_ref.is_valid():
            return
        prev = self.prev_note_ref.get()
        if time() < prev.despawn_time():
            draw_connector(
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
            draw_connector(
                sprite=self.connector_sprite,
                pos=self.lane.pos,
                y=self.y,
                prev_pos=prev_pos,
                prev_y=0,
            )
            draw_note(
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
    def y(self):
        return note_y(self.timescale_group.scaled_time, self.target_scaled_time)

    @property
    def lane(self) -> Lane:
        return self.lane_ref.get()

    @property
    def timescale_group(self) -> TimescaleGroup:
        return self.timescale_group_ref.get()

    @property
    def window(self) -> JudgmentWindow:
        return note_judgment_window

    @property
    def hitbox(self):
        return self.lane.hitbox

    @property
    def bucket(self):
        result = copy(Buckets.tap_note)
        match self.variant:
            case NoteVariant.SINGLE:
                result @= Buckets.tap_note
            case NoteVariant.HOLD_START:
                result @= Buckets.hold_start_note
            case NoteVariant.HOLD_END:
                result @= Buckets.hold_end_note
        return result

    @property
    def body_sprite(self):
        result = copy(Skin.tap_note)
        match self.variant:
            case NoteVariant.SINGLE:
                result @= Skin.tap_note
            case NoteVariant.HOLD_START:
                result @= Skin.hold_start_note
            case NoteVariant.HOLD_END:
                result @= Skin.hold_end_note
        return result

    @property
    def head_sprite(self):
        return Skin.hold_start_note

    @property
    def connector_sprite(self):
        return Skin.connector

    @property
    def particle(self):
        result = copy(Particles.tap_note)
        match self.variant:
            case NoteVariant.SINGLE:
                result @= Particles.tap_note
            case NoteVariant.HOLD_START:
                result @= Particles.hold_note
            case NoteVariant.HOLD_END:
                result @= Particles.hold_note
        return result

    @property
    def hold_particle(self):
        return Particles.hold

    @property
    def prev_start_time(self) -> float:
        if not self.prev_note_ref.is_valid():
            return 1e8
        return self.prev_note_ref.get().start_time

    @property
    def target_time(self) -> float:
        return beat_to_time(self.beat)
