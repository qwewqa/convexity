from __future__ import annotations

from collections.abc import Callable

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
from sonolus.script.runtime import input_offset, time, touches
from sonolus.script.sprite import Sprite
from sonolus.script.stream import Stream
from sonolus.script.timing import beat_to_time
from sonolus.script.values import copy, zeros
from sonolus.script.vec import Vec2

from convexity.common.layout import (
    LanePosition,
    add_backspin,
    adjusted_lane_to_pos,
    lane_hitbox,
    lane_hitbox_pos,
    lane_to_pos,
    note_y,
    touch_pos_to_lane,
)
from convexity.common.note import (
    HoldHandle,
    NoteVariant,
    draw_note_arrow,
    draw_note_body,
    draw_note_connector,
    draw_note_head,
    draw_note_sim_line,
    draw_swing_arrow,
    flick_velocity_threshold,
    note_arrow_sprite,
    note_body_sprite,
    note_bucket,
    note_connector_sprite,
    note_head_sprite,
    note_hold_particle_circular,
    note_hold_particle_linear,
    note_particle_circular,
    note_particle_linear,
    note_window,
    play_hit_effects,
    pulse_note_times,
    pulse_scaled_time,
    schedule_auto_hit_sfx,
    swing_velocity_threshold,
    wave_note_times,
    wave_scaled_time,
)
from convexity.common.options import Options, SoflanMode
from convexity.common.streams import Streams
from convexity.play.config import PlayConfig
from convexity.play.input_manager import input_note_indexes, mark_touch_id_used, mark_touch_used, taps, touch_is_used
from convexity.play.timescale import TimescaleGroup


class Note(PlayArchetype):
    is_scored = True

    variant: NoteVariant = imported()
    beat: float = imported()
    lane: float = imported()
    leniency: float = imported()
    direction: float = imported()
    timescale_group_ref: EntityRef[TimescaleGroup] = imported()
    prev_note_ref: EntityRef[Note] = imported()
    sim_note_ref: EntityRef[Note] = imported()

    touch_id: int = shared_memory()
    y: float = shared_memory()
    pos: LanePosition = shared_memory()
    input_finished: bool = shared_memory()
    finished: bool = shared_memory()
    base_hitbox_pos: LanePosition = shared_memory()
    right_vec: Vec2 = shared_memory()
    hold_handle: HoldHandle = shared_memory()

    target_time: float = entity_data()
    input_target_time: float = entity_data()
    input_time: Interval = entity_data()
    window: JudgmentWindow = entity_data()
    bucket: Bucket = entity_data()
    body_sprite: Sprite = entity_data()
    arrow_sprite: Sprite = entity_data()
    head_sprite: Sprite = entity_data()
    connector_sprite: Sprite = entity_data()
    particle_linear: Particle = entity_data()
    particle_circular: Particle = entity_data()
    hold_particle_linear: Particle = entity_data()
    hold_particle_circular: Particle = entity_data()
    start_time: float = entity_data()
    target_scaled_time: float = entity_data()
    next_note_ref: EntityRef[Note] = entity_data()

    started: bool = entity_memory()
    tracking_lane: float = entity_memory()
    is_tracking: bool = entity_memory()

    finish_time: float = exported()
    judgment: Judgment = exported()

    def preprocess(self):
        if Options.mirror:
            self.lane = -self.lane
            self.direction = -self.direction
        self.leniency += PlayConfig.base_leniency

        if Options.no_flicks:
            match self.variant:
                case NoteVariant.FLICK | NoteVariant.DIRECTIONAL_FLICK:
                    if self.has_prev:
                        self.variant = NoteVariant.HOLD_END
                    else:
                        self.variant = NoteVariant.SINGLE

        if Options.boxy_sliders and self.has_prev and self.variant != NoteVariant.HOLD_ANCHOR:
            while self.prev.has_prev and self.prev.variant == NoteVariant.HOLD_ANCHOR:
                self.prev_note_ref @= self.prev.prev_note_ref
            self.prev.direction = self.lane - self.prev.lane

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
        self.particle_linear @= note_particle_linear(self.variant, self.direction)
        self.particle_circular @= note_particle_circular(self.variant, self.direction)
        self.hold_particle_linear @= note_hold_particle_linear(self.variant)
        self.hold_particle_circular @= note_hold_particle_circular(self.variant)

        self.start_time, self.target_scaled_time = self.get_note_times()

        self.base_hitbox_pos @= lane_hitbox_pos(
            self.lane,
            self.leniency,
            self.direction if self.variant == NoteVariant.DIRECTIONAL_FLICK else 0,
        )
        reference_hitbox = lane_hitbox(LanePosition(self.base_hitbox_pos.mid - 0.5, self.base_hitbox_pos.mid + 0.5))
        self.right_vec = (reference_hitbox.br - reference_hitbox.bl).normalize()

        if self.variant != NoteVariant.HOLD_ANCHOR:
            schedule_auto_hit_sfx(self.variant, Judgment.PERFECT, self.target_time)

        if self.has_prev and not (Options.boxy_sliders and self.variant == NoteVariant.HOLD_ANCHOR):
            self.prev_note_ref.get().next_note_ref @= self.ref()

        self.tracking_lane = 0
        self.is_tracking = False

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
        self.update_pos()
        if self.has_sim and self.sim_note.is_waiting:
            self.sim_note.update_pos()
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
        if self.has_prev and self.prev.is_despawned and self.prev.touch_id == 0:
            if self.hold_handle == self.prev.hold_handle:
                self.hold_handle.destroy()
            self.prev.hold_handle.destroy()
        if self.has_prev and self.prev.hold_handle != self.hold_handle and self.prev.hold_handle.is_active:
            self.hold_handle.destroy()
            self.hold_handle @= self.prev.hold_handle
        self.update_particle()

    def update_parallel(self):
        if self.despawn:
            return
        if Options.boxy_sliders and self.variant == NoteVariant.HOLD_ANCHOR:
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
            if prev.touch_id == 0:
                return
            prev_pos = zeros(LanePosition)
            if Options.tracking_sliders and self.is_tracking:
                prev_pos @= lane_to_pos(self.tracking_lane)
            elif Options.boxy_sliders:
                prev_pos @= self.pos
            else:
                prev_target_time = prev.target_time
                target_time = self.target_time
                progress = max(0, unlerp(prev_target_time, target_time, time()))
                prev_pos @= lerp(prev.pos, self.pos, progress)
            draw_note_connector(
                sprite=self.connector_sprite,
                pos=self.pos,
                y=self.y,
                prev_pos=prev_pos,
                prev_y=0,
            )
            draw_note_head(
                sprite=self.head_sprite,
                pos=prev_pos,
                y=0,
            )
        elif self.variant != NoteVariant.HOLD_END and self.prev.touch_id != 0:
            draw_note_head(
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
            case NoteVariant.HOLD_START | NoteVariant.HOLD_TICK if Options.boxy_sliders and self.direction != 0:
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

    def update_particle(self):
        if Options.boxy_sliders and self.variant == NoteVariant.HOLD_ANCHOR:
            return
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
            if self.hold_handle != prev.hold_handle:
                self.hold_handle.destroy()
                self.hold_handle @= prev.hold_handle
        elif time() < self.target_time:
            if prev.touch_id == 0:
                self.hold_handle.destroy()
            else:
                prev_target_time = prev.target_time
                target_time = self.target_time
                progress = max(0, unlerp(prev_target_time, target_time, time()))
                prev_pos = zeros(LanePosition)
                if Options.tracking_sliders and self.is_tracking:
                    prev_pos @= lane_to_pos(self.tracking_lane)
                elif Options.boxy_sliders:
                    prev_pos @= self.pos
                else:
                    prev_pos @= lerp(prev.pos, self.pos, progress)
                self.hold_handle.update(
                    particle_linear=self.hold_particle_linear,
                    particle_circular=self.hold_particle_circular,
                    pos=prev_pos,
                )
        elif self.variant != NoteVariant.HOLD_END and self.prev.touch_id != 0:
            self.hold_handle.update(
                particle_linear=self.hold_particle_linear,
                particle_circular=self.hold_particle_circular,
                pos=self.pos,
            )
        else:
            pass

    def touch(self):
        if self.has_prev and not (self.prev.is_despawned or self.prev.input_finished):
            return
        if self.has_prev and self.prev.touch_id != 0:
            mark_touch_id_used(self.prev.touch_id)
        if self.touch_id != 0:
            mark_touch_id_used(self.touch_id)
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
        if self.touch_id != 0:
            for touch in touches():
                if touch.id == self.touch_id:
                    self.tracking_lane = touch_pos_to_lane(touch.position)
                    self.tracking_stream[time()] = self.tracking_lane
                    self.is_tracking = True
                    break

    def handle_tap_input(self):
        if time() not in self.input_time:
            return
        hitbox = self.get_hitbox()
        for touch in taps():
            if not hitbox(touch.position):
                continue
            mark_touch_used(touch)
            self.touch_id = touch.id
            self.complete(touch.start_time)
            return

    def handle_release_input(self):
        if self.prev.touch_id != 0:
            self.touch_id = self.prev.touch_id
        if self.touch_id == 0:
            return
        hitbox = self.get_hitbox()
        for touch in touches():
            if touch.id != self.touch_id:
                continue
            if not touch.ended:
                return
            if touch.time >= self.input_time.start and hitbox(touch.position):
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
                if self.has_prev and self.prev.touch_id != 0:
                    for touch in touches():
                        if touch.id != self.prev.touch_id:
                            continue
                        if touch.ended:
                            self.fail(touch.time)
                            return
                        break
                    else:
                        self.fail(time() - input_offset())
                return
            hitbox = self.get_hitbox()
            if self.has_prev and self.prev.touch_id != 0:
                for touch in touches():
                    if touch.id == self.prev.touch_id:
                        if hitbox(touch.position):
                            mark_touch_used(touch)
                            self.touch_id = touch.id
                            break
                        elif touch.ended:
                            self.fail(touch.time)
                            return
                        else:
                            return
                else:
                    self.fail(time() - input_offset())
            else:
                for touch in taps():
                    if not hitbox(touch.position):
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
            met_direction = self.direction == 0 or (self.right_vec * self.direction).dot(touch.delta) >= 0
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
                if touch.time >= self.target_time:
                    # The touch has just met the flick criteria after the target time.
                    self.complete(
                        touch.time
                        if touch.start_time < (self.window + self.target_time).perfect.start
                        else touch.start_time
                    )
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
        hitbox = self.get_hitbox()
        if self.touch_id == 0:
            if self.has_prev and self.prev.touch_id != 0:
                self.touch_id = self.prev.touch_id
            elif time() not in self.input_time:
                return
            else:
                for touch in taps():
                    if not hitbox(touch.position):
                        continue
                    mark_touch_used(touch)
                    self.touch_id = touch.id
                    break
                else:
                    return
        for touch in touches():
            if touch.id != self.touch_id:
                continue
            if hitbox(touch.position):
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
        hitbox = self.get_hitbox()
        for touch in touches():
            if self.touch_id != 0 and touch.id != self.touch_id:
                continue
            if self.touch_id == 0 and touch_is_used(touch):
                continue
            velocity_met = touch.velocity.magnitude >= target_velocity
            hitbox_met = hitbox(touch.position) or hitbox(touch.prev_position)
            met = (velocity_met or touch.started) and hitbox_met
            if self.started:
                if time() >= self.input_target_time:
                    # The touch has continuously met the swing criteria into the target time.
                    self.touch_id = touch.id
                    mark_touch_used(touch)
                    self.complete(self.target_time)
                elif not hitbox_met or touch.ended:
                    # The touch has stopped meeting the swing criteria or ended before the target time.
                    # It's ok if the touch has become too slow though, so we wait until the target time in that case.
                    self.touch_id = touch.id
                    mark_touch_used(touch)
                    self.complete(touch.time)
                else:
                    # The touch has continuously met the swing criteria, but we haven't reached the target time yet.
                    pass
            elif met:
                if touch.time >= self.input_target_time:
                    # The touch has just met the swing criteria after the target time.
                    self.touch_id = touch.id
                    mark_touch_used(touch)
                    self.complete(touch.time)
                elif touch.time >= self.input_time.start:
                    # The touch has just met the swing criteria before the target time.
                    self.touch_id = touch.id
                    mark_touch_used(touch)
                    self.started = True
                    if touch.ended:
                        self.complete(touch.time)
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

    def get_hitbox(self) -> Callable[[Vec2], bool]:
        hitbox_pos = copy(self.base_hitbox_pos)
        if self.touch_id != 0 or (self.has_prev and self.prev.touch_id != 0):
            pass
        else:
            own_mid = self.base_hitbox_pos.mid
            for other_index in input_note_indexes:
                if other_index == self.index:
                    continue
                other = Note.at(other_index)
                if other.input_finished or abs(other.target_time - self.target_time) > 0.005 or other.touch_id != 0:
                    continue
                other_mid = other.base_hitbox_pos.mid
                if other_mid > own_mid and self.base_hitbox_pos.right > other.base_hitbox_pos.left:
                    hitbox_pos.right = min(
                        hitbox_pos.right,
                        (self.base_hitbox_pos.right + other.base_hitbox_pos.left) / 2,
                    )
                elif other_mid < own_mid and self.base_hitbox_pos.left < other.base_hitbox_pos.right:
                    hitbox_pos.left = max(
                        hitbox_pos.left,
                        (self.base_hitbox_pos.left + other.base_hitbox_pos.right) / 2,
                    )
                else:
                    pass
        # Splitting up the hitbox to prevent issues with it wrapping around with arc and high tilt
        left_hitbox = lane_hitbox(LanePosition(left=hitbox_pos.left, right=hitbox_pos.mid + 1e-3))
        right_hitbox = lane_hitbox(LanePosition(left=hitbox_pos.mid, right=hitbox_pos.right))

        def hitbox(position: Vec2):
            return left_hitbox.contains_point(position) or right_hitbox.contains_point(position)

        return hitbox

    def complete(self, actual_time: float):
        judgment = self.window.judge(actual=actual_time, target=self.target_time)
        self.judgment = judgment
        self.result.judgment = judgment
        self.result.accuracy = actual_time - self.target_time
        self.result.bucket @= self.bucket
        self.result.bucket_value = self.result.accuracy * 1000
        if self.variant != NoteVariant.HOLD_ANCHOR:
            play_hit_effects(
                variant=self.variant,
                note_particle_linear=self.particle_linear,
                note_particle_circular=self.particle_circular,
                pos=self.pos,
                judgment=judgment,
            )
        self.despawn = True
        self.finished = True
        self.input_finished = True
        if Options.backspin:
            match self.variant:
                case NoteVariant.FLICK | NoteVariant.DIRECTIONAL_FLICK:
                    add_backspin()
                case _:
                    pass

    def fail(self, actual_time: float):
        judgment = Judgment.MISS
        self.judgment = judgment
        self.result.judgment = judgment
        self.result.accuracy = actual_time - self.target_time
        self.result.bucket @= self.bucket
        self.result.bucket_value = self.result.accuracy * 1000
        self.touch_id = 0
        self.despawn = True
        self.finished = True
        self.input_finished = True

    def terminate(self):
        if not self.has_next or self.next.hold_handle != self.hold_handle:
            self.hold_handle.destroy_silent()
        self.finish_time = time()

    def update_pos(self):
        if time() > self.target_time and Options.sticky_notes:
            self.y = 0
        else:
            self.y = note_y(self.scaled_time, self.target_scaled_time)
        self.pos @= adjusted_lane_to_pos(self.lane, self.scaled_time, self.target_scaled_time)

    @property
    def timescale_group(self) -> TimescaleGroup:
        return self.timescale_group_ref.get()

    def get_note_times(self):
        match Options.soflan_mode:
            case SoflanMode.PULSE:
                start_time, target_scaled_time = pulse_note_times(self.beat)
            case SoflanMode.WAVE:
                start_time, target_scaled_time = wave_note_times(self.beat)
            case _:
                start_time, target_scaled_time = self.timescale_group.get_note_times(self.target_time)
        return start_time, target_scaled_time

    @property
    def scaled_time(self) -> float:
        match Options.soflan_mode:
            case SoflanMode.PULSE:
                return pulse_scaled_time()
            case SoflanMode.WAVE:
                return wave_scaled_time(self.beat)
            case _:
                return self.timescale_group.scaled_time

    @property
    def prev(self) -> Note:
        return self.prev_note_ref.get()

    @property
    def has_prev(self) -> bool:
        return self.prev_note_ref.index > 0

    @property
    def prev_start_time(self) -> float:
        if not self.has_prev:
            return 1e8
        return self.prev_note_ref.get().start_time

    @property
    def sim_note(self) -> Note:
        return self.sim_note_ref.get()

    @property
    def has_sim(self) -> bool:
        return self.sim_note_ref.index > 0

    @property
    def sim_start_time(self) -> float:
        if not self.has_sim:
            return 1e8
        return self.sim_note.start_time

    @property
    def has_next(self) -> bool:
        return self.next_note_ref.index > 0

    @property
    def next(self) -> Note:
        return self.next_note_ref.get()

    @property
    def tracking_stream(self) -> Stream[float]:
        return Streams.note_touch_tracking[self.index]


class UnscoredNote(Note):
    is_scored = False
