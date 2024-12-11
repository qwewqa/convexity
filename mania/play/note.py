from __future__ import annotations

from sonolus.script.archetype import (
    EntityRef,
    PlayArchetype,
    entity_data,
    entity_memory,
    exported,
    imported,
    shared_memory,
)
from sonolus.script.bucket import Bucket, Judgment, JudgmentWindow
from sonolus.script.interval import Interval, lerp, unlerp
from sonolus.script.particle import Particle
from sonolus.script.quad import Quad
from sonolus.script.runtime import input_offset, screen, time, touches
from sonolus.script.sprite import Sprite
from sonolus.script.timing import beat_to_time
from sonolus.script.values import copy, zeros
from sonolus.script.vec import Vec2

from mania.common.layout import (
    HitboxPoints,
    LanePosition,
    lane_hitbox,
    lane_hitbox_points,
    lane_to_pos,
    note_y,
)
from mania.common.note import (
    HoldHandle,
    NoteVariant,
    draw_note_arrow,
    draw_note_body,
    draw_note_connector,
    draw_note_sim_line,
    draw_swing_arrow,
    flick_velocity_threshold,
    note_arrow_sprite,
    note_body_sprite,
    note_bucket,
    note_connector_sprite,
    note_head_sprite,
    note_hold_particle,
    note_particle,
    note_window,
    play_hit_effects,
    schedule_auto_hit_sfx,
    swing_velocity_threshold,
)
from mania.common.options import Options
from mania.play.input_manager import input_note_indexes, mark_touch_used, taps
from mania.play.timescale import TimescaleGroup


class Note(PlayArchetype):
    is_scored = True

    variant: NoteVariant = imported()
    beat: float = imported()
    lane: float = imported()
    leniency: float = imported()
    direction: int = imported()
    timescale_group_ref: EntityRef[TimescaleGroup] = imported()
    prev_note_ref: EntityRef[Note] = imported()
    sim_note_ref: EntityRef[Note] = imported()

    touch_id: int = shared_memory()
    y: float = shared_memory()
    input_finished: bool = shared_memory()
    finished: bool = shared_memory()
    hitbox: Quad = shared_memory()
    hitbox_points: HitboxPoints = shared_memory()

    pos: LanePosition = entity_data()
    target_time: float = entity_data()
    input_target_time: float = entity_data()
    input_time: Interval = entity_data()
    window: JudgmentWindow = entity_data()
    bucket: Bucket = entity_data()
    body_sprite: Sprite = entity_data()
    arrow_sprite: Sprite = entity_data()
    head_sprite: Sprite = entity_data()
    connector_sprite: Sprite = entity_data()
    particle: Particle = entity_data()
    hold_particle: Particle = entity_data()
    has_prev: bool = entity_data()
    has_sim: bool = entity_data()
    start_time: float = entity_data()
    target_scaled_time: float = entity_data()

    started: bool = entity_memory()
    hold_handle: HoldHandle = entity_memory()

    finish_time: float = exported()

    def preprocess(self):
        if Options.mirror:
            self.lane = -self.lane
            self.direction = -self.direction
        self.leniency = max(self.leniency + Options.leniency, 0.2)

        self.pos @= lane_to_pos(self.lane)
        self.target_time = beat_to_time(self.beat)
        self.input_target_time = self.target_time + input_offset()
        self.input_time = note_window(self.variant).good + self.input_target_time
        self.window @= note_window(self.variant)
        self.bucket @= note_bucket(self.variant)
        self.body_sprite @= note_body_sprite(self.variant, self.direction)
        self.arrow_sprite @= note_arrow_sprite(self.variant, self.direction)
        self.head_sprite @= note_head_sprite(self.variant)
        self.connector_sprite @= note_connector_sprite(self.variant)
        self.particle @= note_particle(self.variant, self.direction)
        self.hold_particle @= note_hold_particle(self.variant)
        self.has_prev = self.prev_note_ref.index > 0
        self.has_sim = self.sim_note_ref.index > 0

        self.start_time, self.target_scaled_time = self.timescale_group.get_note_times(self.target_time)

        if self.variant == NoteVariant.HOLD_ANCHOR:
            self.hitbox @= screen().as_quad()
        else:
            self.hitbox @= lane_hitbox(
                self.lane,
                self.leniency * (1 + Options.spread),
                self.direction if self.variant == NoteVariant.DIRECTIONAL_FLICK else 0,
            )
            self.hitbox_points @= lane_hitbox_points(
                self.lane,
                self.leniency * (1 + Options.spread),
                self.direction if self.variant == NoteVariant.DIRECTIONAL_FLICK else 0,
            )

        if self.variant != NoteVariant.HOLD_ANCHOR:
            schedule_auto_hit_sfx(Judgment.PERFECT, self.target_time)

    def spawn_time(self) -> float:
        return min(self.start_time, self.prev_start_time, self.sim_start_time)

    def spawn_order(self) -> float:
        return self.spawn_time()

    def should_spawn(self) -> bool:
        return time() >= self.spawn_time()

    def update_sequential(self):
        if self.missed_timing() or self.chain_miss():
            self.despawn = True
            self.finished = True
            self.input_finished = True
        self.y = note_y(self.timescale_group.scaled_time, self.target_scaled_time)
        if self.has_sim and self.sim_note.is_waiting:
            self.sim_note.y = note_y(self.sim_note.timescale_group.scaled_time, self.sim_note.target_scaled_time)
        if self.variant == NoteVariant.HOLD_ANCHOR:
            self.input_finished = self.prev.input_finished or self.prev.is_despawned
        if (
            not self.input_finished
            and self.touch_id == 0
            and (
                not self.has_prev or (self.prev.touch_id == 0 and (self.prev.input_finished or self.prev.is_despawned))
            )
            and time() >= self.input_time.start
            and not input_note_indexes.is_full()
            and self.variant != NoteVariant.HOLD_ANCHOR
        ):
            input_note_indexes.append(self.index)

    def update_parallel(self):
        if self.despawn:
            return
        self.draw_body()
        self.draw_connector()
        self.draw_arrow()
        self.draw_sim_line()

    def missed_timing(self) -> bool:
        return time() > self.input_time.end

    def chain_miss(self) -> bool:
        if not self.has_prev:
            return False
        return self.prev.finished and self.prev.touch_id == 0 and self.variant != NoteVariant.HOLD_TICK

    def draw_body(self):
        if self.variant != NoteVariant.HOLD_ANCHOR:
            draw_note_body(
                sprite=self.body_sprite,
                pos=self.pos,
                y=self.y,
            )

    def draw_connector(self):
        if not self.has_prev:
            return
        prev_finished = True
        ref = copy(self.prev_note_ref)
        for _ in range(20):
            # Handle a tick finishing before previous anchors by looking further back.
            prev_finished = prev_finished and ref.get().finished
            if not prev_finished:
                break
            if not ref.get().has_prev:
                break
            ref @= ref.get().prev_note_ref
        if prev_finished:
            ref @= self.prev_note_ref
        prev = ref.get()
        if not prev_finished:
            draw_note_connector(
                sprite=self.connector_sprite,
                pos=self.pos,
                y=self.y,
                prev_pos=prev.pos,
                prev_y=prev.y,
            )
        elif time() < self.target_time:
            prev_target_time = prev.target_time
            target_time = self.target_time
            progress = max(0, unlerp(prev_target_time, target_time, time()))
            prev_pos = lerp(prev.pos, self.pos, progress)
            draw_note_connector(
                sprite=self.connector_sprite,
                pos=self.pos,
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
        elif self.variant != NoteVariant.HOLD_END:
            draw_note_body(
                sprite=self.head_sprite,
                pos=self.pos,
                y=0,
            )

    def draw_arrow(self):
        match self.variant:
            case NoteVariant.FLICK | NoteVariant.DIRECTIONAL_FLICK:
                draw_note_arrow(
                    sprite=self.arrow_sprite,
                    direction=self.direction,
                    pos=self.pos,
                    y=self.y,
                )
            case NoteVariant.SWING:
                draw_swing_arrow(
                    sprite=self.arrow_sprite,
                    direction=self.direction,
                    pos=self.pos,
                    y=self.y,
                )
            case _:
                pass

    def draw_sim_line(self):
        if not self.has_sim:
            return
        sim = self.sim_note
        if sim.is_despawned:
            return
        draw_note_sim_line(
            pos=self.pos,
            y=self.y,
            sim_pos=sim.pos,
            sim_y=sim.y,
        )

    def touch(self):
        if self.has_prev and not (self.prev.is_despawned or self.prev.input_finished):
            return
        match self.variant:
            case NoteVariant.SINGLE | NoteVariant.HOLD_START:
                self.handle_tap_input()
            case NoteVariant.HOLD_END:
                if Options.auto_release_holds:
                    self.handle_hold_input()
                else:
                    self.handle_release_input()
            case NoteVariant.HOLD_TICK:
                self.handle_hold_input()
            case NoteVariant.HOLD_ANCHOR:
                self.handle_anchor_input()
            case NoteVariant.FLICK | NoteVariant.DIRECTIONAL_FLICK:
                self.handle_flick_input()
            case NoteVariant.SWING:
                self.handle_swing_input()

    def handle_tap_input(self):
        if time() not in self.input_time:
            return
        for touch in taps():
            if not self.hitbox_contains(touch.position):
                continue
            mark_touch_used(touch)
            self.touch_id = touch.id
            self.complete(touch.start_time)
            return

    def handle_release_input(self):
        touch_id = self.prev.touch_id
        if touch_id == 0:
            return
        self.touch_id = touch_id
        for touch in touches():
            if touch.id != touch_id:
                continue
            if not touch.ended:
                return
            if time() >= self.input_time.start and self.hitbox_contains(touch.position):
                self.complete(touch.time)
            else:
                self.fail(touch.time)
            return
        if time() >= self.input_time.start:
            self.complete(time() - input_offset())
        else:
            self.fail(time() - input_offset())

    def handle_flick_input(self):
        if self.touch_id == 0:
            if time() not in self.input_time:
                return
            if self.has_prev and self.prev.touch_id != 0:
                for touch in touches():
                    if touch.id == self.prev.touch_id and self.hitbox_contains(touch.position):
                        mark_touch_used(touch)
                        self.touch_id = touch.id
                        break
                else:
                    return
            else:
                for touch in taps():
                    if not self.hitbox_contains(touch.position):
                        continue
                    mark_touch_used(touch)
                    self.touch_id = touch.id
                    break
                else:
                    return
        target_velocity = flick_velocity_threshold(self.direction)
        for touch in touches():
            if touch.id != self.touch_id:
                continue
            met_velocity = touch.velocity.magnitude >= target_velocity
            met_direction = (
                self.direction == 0 or ((self.hitbox.br - self.hitbox.bl) * self.direction).dot(touch.delta) > 0
            )
            met = met_velocity and met_direction
            if self.started:
                if time() >= self.input_target_time:
                    # The touch has continuously met the flick criteria into the target time.
                    self.complete(self.target_time)
                elif (not met and not self.has_prev) or touch.ended:
                    # The touch has stopped meeting the flick criteria or ended before the target time.
                    # We also make an exception for hold-flicks.
                    self.complete(touch.time)
                else:
                    # The touch has continuously met the flick criteria, but we haven't reached the target time yet.
                    pass
            elif met:
                if touch.time >= self.input_target_time:
                    # The touch has just met the flick criteria after the target time.
                    self.complete(touch.time)
                elif touch.time >= self.input_time.start:
                    # The touch has just met the flick criteria before the target time.
                    self.started = True
                else:
                    # The touch has just met the flick criteria before the input time.
                    pass
            elif touch.ended:
                # The touch has ended without ever meeting the flick criteria.
                self.fail(touch.time)
            else:
                # The touch is ongoing, but it's never met the flick criteria.
                pass
            return
        self.fail(time() - input_offset())

    def handle_hold_input(self):
        if self.touch_id == 0:
            if time() not in self.input_time:
                return
            if self.has_prev and self.prev.touch_id != 0:
                for touch in touches():
                    if touch.id == self.prev.touch_id and self.hitbox_contains(touch.position):
                        mark_touch_used(touch)
                        self.touch_id = touch.id
                        break
                else:
                    return
            else:
                for touch in taps():
                    if not self.hitbox_contains(touch.position):
                        continue
                    mark_touch_used(touch)
                    self.touch_id = touch.id
                    break
                else:
                    return
        for touch in touches():
            if touch.id != self.touch_id:
                continue
            if self.hitbox_contains(touch.position):
                if touch.ended:
                    # The touch has ended in the hitbox.
                    if time() >= self.input_time.start:
                        self.complete(touch.time)
                    else:
                        self.fail(touch.time)
                elif time() >= self.input_target_time:
                    # The touch is in the hitbox and we've reached the target time.
                    if self.started:
                        # And it's been in the hitbox continuously.
                        self.complete(self.target_time)
                    else:
                        # But it just entered the hitbox.
                        self.complete(time() - input_offset())
                elif time() >= self.input_time.start:
                    # The touch is in the hitbox, but we haven't reached the target time yet.
                    self.started = True
                else:
                    # The touch is ongoing and in the hitbox, but it's not yet in the input time.
                    pass
            elif self.started:
                # The touch was in the hitbox, but moved out, so it counts as a release.
                # self.started will only be true if the input start time has been reached.
                self.complete(time() - input_offset())
            elif touch.ended:
                # The touch ended without ever being in the hitbox within the input time.
                self.fail(touch.time)
            else:
                # The touch is ongoing, but it's never been in the hitbox.
                pass
            return
        if time() >= self.input_time.start:
            self.complete(time() - input_offset())
        else:
            self.fail(time() - input_offset())

    def handle_anchor_input(self):
        if self.prev.touch_id == 0:
            self.fail(time() - input_offset())
        self.touch_id = self.prev.touch_id
        for touch in touches():
            if touch.id == self.touch_id and not touch.ended:
                break
        else:
            self.fail(time() - input_offset())
        if time() >= self.target_time:
            self.complete(time() - input_offset())

    def handle_swing_input(self):
        if self.has_prev and self.prev.touch_id != 0:
            self.touch_id = self.prev.touch_id
        target_velocity = swing_velocity_threshold()
        for touch in touches():
            if self.touch_id != 0 and touch.id != self.touch_id:
                continue
            met = touch.velocity.magnitude >= target_velocity and (
                self.hitbox_contains(touch.position) or self.hitbox_contains(touch.prev_position)
            )
            if self.started:
                if time() >= self.input_target_time:
                    # The touch has continuously met the swing criteria into the target time.
                    self.touch_id = touch.id
                    self.complete(self.target_time)
                elif not met or touch.ended:
                    # The touch has stopped meeting the swing criteria or ended before the target time.
                    self.touch_id = touch.id
                    self.complete(touch.time)
                else:
                    # The touch has continuously met the swing criteria, but we haven't reached the target time yet.
                    pass
            elif met:
                if touch.time >= self.input_target_time:
                    # The touch has just met the swing criteria after the target time.
                    self.touch_id = touch.id
                    self.complete(touch.time)
                elif touch.time >= self.input_time.start:
                    # The touch has just met the swing criteria before the target time.
                    self.touch_id = touch.id
                    self.started = True
                else:
                    # The touch has just met the swing criteria before the input time.
                    pass
            elif touch.ended:
                if self.touch_id != 0:
                    # The touch has ended without ever meeting the swing criteria,
                    # and there is an ongoing previous touch.
                    self.fail(touch.time)
                else:
                    # The touch has ended without ever meeting the swing criteria,
                    # so we can ignore it.
                    pass
            else:
                # The touch is ongoing, but it's never met the swing criteria.
                pass
            if self.touch_id != 0:
                return
        if self.touch_id != 0:
            # We have a touch from a previous note, but it has gone missing.
            self.fail(time() - input_offset())

    def hitbox_contains(self, position: Vec2) -> bool:
        if not self.hitbox.contains_point(position):
            return False
        if self.touch_id != 0 or (self.has_prev and self.prev.touch_id != 0):
            return True
        own_mid = self.hitbox_points.mid
        for other_index in input_note_indexes:
            if other_index == self.index:
                continue
            other = Note.at(other_index)
            if (
                other.input_finished
                or not other.hitbox.contains_point(position)
                or other.beat != self.beat
                or other.touch_id != 0
            ):
                continue
            other_mid = other.hitbox_points.mid
            h_mid = other_mid - own_mid
            if h_mid.magnitude < 1e-3:
                continue
            p1 = zeros(Vec2)
            p2 = zeros(Vec2)
            if (self.hitbox_points.left - own_mid).dot(h_mid) > 0:
                p1 @= other.hitbox_points.right
                p2 @= self.hitbox_points.left
            else:
                p1 @= other.hitbox_points.left
                p2 @= self.hitbox_points.right
            h_inner = p2 - p1
            if h_inner.magnitude < 1e-3:
                continue
            cutoff = h_inner.magnitude / 2
            h_inner @= h_inner.normalize()
            proj = (position - p1).dot(h_inner)
            if proj > cutoff:
                return False
        return True

    def complete(self, actual_time: float):
        self.result.judgment = self.window.judge(actual=actual_time, target=self.target_time)
        self.result.accuracy = actual_time - self.target_time
        self.result.bucket @= self.bucket
        self.result.bucket_value = self.result.accuracy * 1000
        if self.variant != NoteVariant.HOLD_ANCHOR:
            play_hit_effects(
                note_particle=self.particle,
                pos=self.pos,
                judgment=self.result.judgment,
            )
        self.despawn = True
        self.finished = True
        self.input_finished = True

    def fail(self, actual_time: float):
        self.result.judgment = Judgment.MISS
        self.result.accuracy = actual_time - self.target_time
        self.result.bucket @= self.bucket
        self.result.bucket_value = self.result.accuracy * 1000
        self.touch_id = 0
        self.despawn = True
        self.finished = True
        self.input_finished = True

    def terminate(self):
        self.hold_handle.destroy()
        self.finish_time = time()

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

    @property
    def sim_note(self) -> Note:
        return self.sim_note_ref.get()

    @property
    def sim_start_time(self) -> float:
        if not self.has_sim:
            return 1e8
        return self.sim_note.start_time


class UnscoredNote(Note):
    is_scored = False
