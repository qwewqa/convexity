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
from sonolus.script.runtime import is_replay, is_skip, time
from sonolus.script.sprite import Sprite
from sonolus.script.timing import beat_to_time
from sonolus.script.values import copy

from convexity.common.layout import (
    LanePosition,
    adjusted_lane_to_pos,
    lane_to_pos,
    note_y,
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
    note_arrow_sprite,
    note_body_sprite,
    note_bucket,
    note_connector_sprite,
    note_head_sprite,
    note_hold_particle,
    note_particle,
    note_window,
    play_watch_hit_effects,
    pulse_note_times,
    pulse_scaled_time,
    schedule_watch_hit_effects,
    wave_note_times,
    wave_scaled_time,
)
from convexity.common.options import Options, SoflanMode
from convexity.watch.task import BackspinTask
from convexity.watch.timescale import TimescaleGroup


class Note(WatchArchetype):
    is_scored = True

    variant: NoteVariant = imported()
    beat: float = imported()
    lane: float = imported()
    direction: float = imported()
    timescale_group_ref: EntityRef[TimescaleGroup] = imported()
    prev_note_ref: EntityRef[Note] = imported()
    sim_note_ref: EntityRef[Note] = imported()

    y: float = shared_memory()
    pos: LanePosition = shared_memory()
    hold_handle: HoldHandle = shared_memory()

    target_time: float = entity_data()
    window: JudgmentWindow = entity_data()
    bucket: Bucket = entity_data()
    body_sprite: Sprite = entity_data()
    arrow_sprite: Sprite = entity_data()
    head_sprite: Sprite = entity_data()
    connector_sprite: Sprite = entity_data()
    particle: Particle = entity_data()
    hold_particle: Particle = entity_data()
    start_time: float = entity_data()
    target_scaled_time: float = entity_data()
    next_note_ref: EntityRef[Note] = entity_data()

    started: bool = entity_memory()
    needs_init: bool = entity_memory()

    judgment: Judgment = imported()
    accuracy: StandardImport.ACCURACY
    finish_time: float = imported()

    def preprocess(self):
        if Options.mirror:
            self.lane = -self.lane
            self.direction = -self.direction

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
        self.window @= note_window(self.variant)
        self.bucket @= note_bucket(self.variant)
        self.body_sprite @= note_body_sprite(self.variant, self.direction)
        self.arrow_sprite @= note_arrow_sprite(self.variant, self.direction)
        self.head_sprite @= note_head_sprite(self.variant)
        self.connector_sprite @= note_connector_sprite(self.variant)
        self.particle @= note_particle(self.variant, self.direction)
        self.hold_particle @= note_hold_particle(self.variant)

        self.start_time, self.target_scaled_time = self.get_note_times()

        self.result.target_time = self.target_time

        if is_replay():
            self.result.bucket @= self.bucket
            self.result.bucket_value = self.accuracy * 1000
            if self.variant != NoteVariant.HOLD_ANCHOR:
                schedule_watch_hit_effects(self.variant, self.finish_time, self.judgment)
            if Options.backspin and self.judgment != Judgment.MISS:
                match self.variant:
                    case NoteVariant.FLICK | NoteVariant.DIRECTIONAL_FLICK:
                        BackspinTask.spawn(time=self.finish_time)
        else:
            self.result.bucket @= self.bucket
            self.result.bucket_value = 0
            self.judgment = Judgment.PERFECT
            if self.variant != NoteVariant.HOLD_ANCHOR:
                schedule_watch_hit_effects(self.variant, self.target_time, self.judgment)
            if Options.backspin and self.judgment != Judgment.MISS:
                match self.variant:
                    case NoteVariant.FLICK | NoteVariant.DIRECTIONAL_FLICK:
                        BackspinTask.spawn(time=self.target_time)

        if self.has_prev and not (Options.boxy_sliders and self.variant == NoteVariant.HOLD_ANCHOR):
            self.prev_note_ref.get().next_note_ref @= self.ref()

    def spawn_time(self) -> float:
        return min(self.start_time, self.prev_start_time, self.sim_start_time)

    def despawn_time(self) -> float:
        if is_replay():
            return self.finish_time
        else:
            return self.target_time

    def initialize(self):
        self.needs_init = True

    def update_sequential(self):
        if self.needs_init:
            self.hold_handle.destroy()
        self.needs_init = False
        self.update_pos()
        if self.has_sim and time() < self.sim_note.spawn_time():
            self.sim_note.update_pos()
        if self.has_prev and (time() >= self.prev.despawn_time()) and self.prev.judgment == Judgment.MISS:
            if self.hold_handle == self.prev.hold_handle:
                self.hold_handle.destroy()
            self.prev.hold_handle.destroy()
        if self.has_prev and self.prev.hold_handle != self.hold_handle and self.prev.hold_handle.is_active:
            self.hold_handle.destroy()
            self.hold_handle @= self.prev.hold_handle
        if is_skip():
            self.hold_handle.destroy()
            if self.has_prev:
                self.prev.hold_handle.destroy()
        self.update_particle()

    def update_parallel(self):
        if Options.boxy_sliders and self.variant == NoteVariant.HOLD_ANCHOR:
            return
        self.draw_body()
        self.draw_connector()
        self.draw_arrow()
        self.draw_sim_line()

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
            prev_finished = prev_finished and time() >= ref.get().despawn_time()
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
            if prev.judgment == Judgment.MISS:
                return
            prev_target_time = prev.target_time
            target_time = self.target_time
            progress = max(0, unlerp(prev_target_time, target_time, time()))
            prev_pos = lerp(prev.pos, self.pos, progress)
            if Options.boxy_sliders:
                prev_pos @= self.pos
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
        elif self.variant != NoteVariant.HOLD_END and prev.judgment != Judgment.MISS:
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
        if time() >= sim.despawn_time():
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
            prev_finished = prev_finished and time() >= ref.get().despawn_time()
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
            if prev.judgment == Judgment.MISS:
                self.hold_handle.destroy()
            else:
                prev_target_time = prev.target_time
                target_time = self.target_time
                progress = max(0, unlerp(prev_target_time, target_time, time()))
                prev_pos = lerp(prev.pos, self.pos, progress)
                if Options.boxy_sliders:
                    prev_pos @= self.pos
                self.hold_handle.update(
                    particle=self.hold_particle,
                    pos=prev_pos,
                )
        elif self.variant != NoteVariant.HOLD_END and prev.judgment != Judgment.MISS:
            self.hold_handle.update(
                particle=self.hold_particle,
                pos=self.pos,
            )
        else:
            pass

    def terminate(self):
        if not self.has_next:
            self.hold_handle.handle.destroy()
            if self.has_prev:
                ref = copy(self.prev_note_ref)
                while True:
                    ref.get().hold_handle.handle.destroy()
                    if not ref.get().has_prev:
                        break
                    ref @= ref.get().prev_note_ref
        elif self.next.hold_handle != self.hold_handle:
            self.hold_handle.handle.destroy()
        if (not is_replay() or self.judgment != Judgment.MISS) and self.variant != NoteVariant.HOLD_ANCHOR:
            play_watch_hit_effects(
                note_particle=self.particle,
                pos=self.pos,
            )

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


class UnscoredNote(Note):
    is_scored = False


UnscoredNote(variant=1)
