from __future__ import annotations

from sonolus.script.archetype import EntityRef, PreviewArchetype, entity_data, imported
from sonolus.script.sprite import Sprite
from sonolus.script.timing import beat_to_time

from convexity.common.layout import LanePosition, Layer, lane_to_pos
from convexity.common.note import (
    NoteVariant,
    note_arrow_sprite,
    note_body_sprite,
    note_connector_sprite,
    note_head_sprite,
)
from convexity.common.options import Options
from convexity.common.skin import Skin
from convexity.preview.layout import (
    PreviewData,
    arrow_layout,
    connector_layout,
    note_layout,
    sim_line_layout,
    time_to_col,
)


class Note(PreviewArchetype):
    is_scored = True

    variant: NoteVariant = imported()
    beat: float = imported()
    lane: float = imported()
    direction: float = imported()
    prev_note_ref: EntityRef[Note] = imported()
    sim_note_ref: EntityRef[Note] = imported()

    pos: LanePosition = entity_data()
    target_time: float = entity_data()
    body_sprite: Sprite = entity_data()
    arrow_sprite: Sprite = entity_data()
    head_sprite: Sprite = entity_data()
    connector_sprite: Sprite = entity_data()
    next_note_ref: EntityRef[Note] = entity_data()

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
        self.body_sprite @= note_body_sprite(self.variant, self.direction)
        self.arrow_sprite @= note_arrow_sprite(self.variant, self.direction)
        self.head_sprite @= note_head_sprite(self.variant)
        self.connector_sprite @= note_connector_sprite(self.variant)

        PreviewData.last_time = max(PreviewData.last_time, self.target_time)
        PreviewData.last_beat = max(PreviewData.last_beat, self.beat)

        if self.has_prev and not (Options.boxy_sliders and self.variant == NoteVariant.HOLD_ANCHOR):
            self.prev_note_ref.get().next_note_ref @= self.ref()

    def render(self):
        if Options.boxy_sliders and self.variant == NoteVariant.HOLD_ANCHOR:
            return
        self.draw_body()
        self.draw_connector()
        self.draw_arrow()
        self.draw_sim_line()

    def draw_body(self):
        if self.variant == NoteVariant.HOLD_ANCHOR:
            return
        self.body_sprite.draw(
            note_layout(self.pos, self.target_time),
            z=Layer.NOTE - self.target_time / 100 + self.pos.mid / 1000,
        )

    def draw_connector(self):
        if not self.has_prev:
            return
        prev_col = time_to_col(self.prev.target_time)
        own_col = time_to_col(self.target_time)
        for col in range(prev_col, own_col + 1):
            if Options.boxy_sliders:
                horizontal_time = self.prev.target_time + min(0.03, self.target_time - self.prev.target_time)
                horizontal_pos = LanePosition(
                    min(self.pos.left, self.prev.pos.left), max(self.pos.right, self.prev.pos.right)
                )
                self.connector_sprite.draw(
                    connector_layout(horizontal_pos, horizontal_time, horizontal_pos, self.prev.target_time, col),
                    z=Layer.CONNECTOR - self.target_time / 100 + self.pos.mid / 1000,
                    a=Options.connector_alpha,
                )
                if horizontal_time < self.target_time:
                    self.connector_sprite.draw(
                        connector_layout(self.pos, self.target_time, self.pos, horizontal_time, col),
                        z=Layer.CONNECTOR - self.target_time / 100 + self.pos.mid / 1000,
                        a=Options.connector_alpha,
                    )
            else:
                self.connector_sprite.draw(
                    connector_layout(self.pos, self.target_time, self.prev.pos, self.prev.target_time, col),
                    z=Layer.CONNECTOR - self.target_time / 100 + self.pos.mid / 1000,
                    a=Options.connector_alpha,
                )

    def draw_arrow(self):
        match self.variant:
            case NoteVariant.FLICK | NoteVariant.SWING:
                layout = arrow_layout(self.pos, self.target_time, self.direction, y_offset=0.9)
                self.arrow_sprite.draw(
                    layout,
                    z=Layer.ARROW - self.target_time / 100 + self.pos.mid / 1000,
                )
            case NoteVariant.HOLD_START | NoteVariant.HOLD_TICK if Options.boxy_sliders and self.direction != 0:
                layout = arrow_layout(self.pos, self.target_time, self.direction, y_offset=0.9)
                self.arrow_sprite.draw(
                    layout,
                    z=Layer.ARROW - self.target_time / 100 + self.pos.mid / 1000,
                )
            case NoteVariant.DIRECTIONAL_FLICK:
                inc = 1 if self.direction > 0 else -1
                for i in range(1, abs(self.direction) + 1):
                    layout = arrow_layout(
                        self.pos + LanePosition(inc * i, inc * i), self.target_time, self.direction, y_offset=0
                    )
                    self.arrow_sprite.draw(
                        layout,
                        z=Layer.ARROW - self.target_time / 100 + self.pos.mid / 1000,
                    )
            case _:
                pass

    def draw_sim_line(self):
        if not self.has_sim or not Options.sim_lines_enabled:
            return
        layout = sim_line_layout(
            self.pos,
            self.sim_note.pos,
            self.target_time,
        )
        Skin.sim_line.draw(
            layout,
            z=Layer.SIM_LINE - self.target_time / 100 + self.pos.mid / 1000,
        )

    @property
    def prev(self) -> Note:
        return self.prev_note_ref.get()

    @property
    def has_prev(self) -> bool:
        return self.prev_note_ref.index > 0

    @property
    def sim_note(self) -> Note:
        return self.sim_note_ref.get()

    @property
    def has_sim(self) -> bool:
        return self.sim_note_ref.index > 0

    @property
    def has_next(self) -> bool:
        return self.next_note_ref.index > 0

    @property
    def next(self) -> Note:
        return self.next_note_ref.get()


UnscoredNote = Note.derive("UnscoredNote", is_scored=False)
