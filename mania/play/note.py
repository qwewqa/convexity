from __future__ import annotations

from sonolus.script.archetype import (
    EntityRef,
    PlayArchetype,
    entity_memory,
    exported,
    imported,
    shared_memory,
)
from sonolus.script.bucket import Judgment, JudgmentWindow
from sonolus.script.interval import lerp, unlerp
from sonolus.script.runtime import time, touches
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
    play_hit_effects,
    schedule_auto_hit_sfx,
)
from mania.common.options import Options
from mania.play.input_manager import mark_touch_used, taps_in_hitbox
from mania.play.lane import Lane
from mania.play.timescale import TimescaleGroup


class Note(PlayArchetype):
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

    finish_time: float = exported()

    def preprocess(self):
        self.start_time, self.target_scaled_time = self.timescale_group.get_note_times(self.target_time)
        schedule_auto_hit_sfx(Judgment.PERFECT, self.target_time)

    def spawn_time(self) -> float:
        return min(self.start_time, self.prev_start_time)

    def spawn_order(self) -> float:
        return self.spawn_time()

    def should_spawn(self) -> bool:
        return time() >= self.spawn_time()

    def update_parallel(self):
        if self.despawn:
            return
        if self.missed_timing() or self.prev_missed():
            self.despawn = True
            return
        self.draw_body()
        self.draw_connector()

    def missed_timing(self) -> bool:
        return time() > self.input_end_time

    def prev_missed(self) -> bool:
        if not self.prev_note_ref.archetype_matches():
            return False
        prev = self.prev_note_ref.get()
        return prev.is_despawned and prev.touch_id == 0

    def draw_body(self):
        draw_note_body(
            sprite=self.body_sprite,
            pos=self.lane.pos,
            y=self.y,
        )

    def draw_connector(self):
        if not self.prev_note_ref.archetype_matches():
            return
        prev = self.prev_note_ref.get()
        if not prev.is_despawned:
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

    def touch(self):
        match self.variant:
            case NoteVariant.SINGLE:
                self.handle_tap_input()
            case NoteVariant.HOLD_START:
                self.handle_tap_input()
            case NoteVariant.HOLD_END:
                self.handle_release_input()

    def handle_tap_input(self):
        if not (self.input_start_time <= time() <= self.input_end_time):
            return
        for touch in taps_in_hitbox(self.hitbox):
            mark_touch_used(touch)
            self.touch_id = touch.id
            self.complete(touch.start_time)
            return

    def handle_release_input(self):
        touch_id = self.prev_note_ref.get().touch_id
        if touch_id == 0:
            return
        for touch in touches():
            if touch.id != touch_id:
                continue
            if Options.auto_release_holds and time() >= self.target_time and self.hitbox.contains_point(touch.position):
                self.complete(self.target_time)
                return
            if not touch.ended:
                return
            if time() >= self.input_start_time and self.hitbox.contains_point(touch.position):
                self.complete(touch.time)
            else:
                self.fail(touch.time)
            return
        if time() >= self.input_start_time:
            self.complete(time())
        else:
            self.fail(time())

    def complete(self, actual_time: float):
        self.result.judgment = self.window.judge(actual=actual_time, target=self.target_time)
        self.result.accuracy = actual_time - self.target_time
        self.result.bucket @= self.bucket
        self.result.bucket_value = self.result.accuracy * 1000
        play_hit_effects(
            note_particle=self.particle,
            pos=self.lane.pos,
            judgment=self.result.judgment,
        )
        self.despawn = True

    def fail(self, actual_time: float):
        self.result.judgment = Judgment.MISS
        self.result.accuracy = actual_time - self.target_time
        self.result.bucket @= self.bucket
        self.result.bucket_value = self.result.accuracy * 1000
        self.despawn = True

    def terminate(self):
        self.hold_handle.destroy()
        self.finish_time = time()

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
    def target_time(self) -> float:
        return beat_to_time(self.beat)

    @property
    def input_start_time(self) -> float:
        return self.target_time + self.window.start

    @property
    def input_end_time(self) -> float:
        return self.target_time + self.window.end

    @property
    def hitbox(self):
        return self.lane.hitbox

    @property
    def window(self) -> JudgmentWindow:
        return note_window(self.variant)

    @property
    def bucket(self):
        return note_bucket(self.variant)

    @property
    def body_sprite(self):
        return note_body_sprite(self.variant)

    @property
    def head_sprite(self):
        return note_head_sprite(self.variant)

    @property
    def connector_sprite(self):
        return note_connector_sprite(self.variant)

    @property
    def particle(self):
        return note_particle(self.variant)

    @property
    def hold_particle(self):
        return note_hold_particle(self.variant)

    @property
    def prev_start_time(self) -> float:
        if not self.prev_note_ref.index > 0:
            return 1e8
        return self.prev_note_ref.get().start_time


class UnscoredNote(Note):
    is_scored = False
