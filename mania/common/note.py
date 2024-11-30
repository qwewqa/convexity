from sonolus.script.bucket import Judgment
from sonolus.script.particle import Particle, ParticleHandle
from sonolus.script.record import Record
from sonolus.script.sprite import Sprite

from mania.common.effect import SFX_DISTANCE, Effects
from mania.common.layout import (
    LanePosition,
    Layer,
    Layout,
    connector_layout,
    lane_layout,
    note_layout,
    note_particle_layout,
)
from mania.common.options import Options
from mania.common.particle import Particles


def draw_note(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_length):
        return
    layout = note_layout(pos, y)
    sprite.draw(layout, z=Layer.NOTE + y + pos.mid / 100)


def draw_connector(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
    prev_pos: LanePosition,
    prev_y: float,
):
    if prev_y < Layout.min_safe_y and y < Layout.min_safe_y:
        return
    if prev_y > Layout.lane_length and y > Layout.lane_length:
        return
    layout = connector_layout(
        pos=pos,
        y=y,
        prev_pos=prev_pos,
        prev_y=prev_y,
    )
    sprite.draw(layout, z=Layer.CONNECTOR + max(y, prev_y) + pos.mid / 100, a=Options.connector_alpha)


def play_hit_effects(
    note_particle: Particle,
    pos: LanePosition,
    judgment: Judgment,
):
    play_hit_sfx(judgment)
    play_hit_particle(note_particle, pos)


def play_hit_sfx(judgment: Judgment):
    if not Options.sfx_enabled or Options.auto_sfx:
        return
    match judgment:
        case Judgment.PERFECT:
            Effects.perfect.play(SFX_DISTANCE)
        case Judgment.GREAT:
            Effects.great.play(SFX_DISTANCE)
        case Judgment.GOOD:
            Effects.good.play(SFX_DISTANCE)


def schedule_auto_hit_sfx(judgment: Judgment, target_time: float):
    if not Options.auto_sfx:
        return
    schedule_hit_sfx(judgment, target_time)


def schedule_hit_sfx(judgment: Judgment, target_time: float):
    if not Options.sfx_enabled:
        return
    match judgment:
        case Judgment.PERFECT:
            Effects.perfect.schedule(target_time, SFX_DISTANCE)
        case Judgment.GREAT:
            Effects.great.schedule(target_time, SFX_DISTANCE)
        case Judgment.GOOD:
            Effects.good.schedule(target_time, SFX_DISTANCE)


def play_hit_particle(
    note_particle: Particle,
    pos: LanePosition,
):
    if Options.note_effect_enabled:
        note_particle.spawn(
            note_particle_layout(pos, scale=0.6),
            duration=0.5,
        )
    if Options.lane_effect_enabled:
        Particles.lane.spawn(
            lane_layout(pos),
            duration=0.2,
        )


class HoldHandle(Record):
    handle: ParticleHandle

    def update(self, particle: Particle, pos: LanePosition):
        if not Options.note_effect_enabled:
            return
        if self.handle.id == 0:
            self.handle @= particle.spawn(
                note_particle_layout(pos, scale=0.4),
                duration=1.0,
                loop=True,
            )
        else:
            self.handle.move(note_particle_layout(pos, scale=0.4))

    def destroy(self):
        if self.handle.id != 0:
            self.handle.destroy()
