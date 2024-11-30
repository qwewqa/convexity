from sonolus.script.bucket import Judgment
from sonolus.script.particle import Particle, ParticleHandle
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
from mania.common.particle import Particles


def draw_note(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
):
    if not (Layout.min_safe_y <= y <= Layout.lane_height):
        return
    layout = note_layout(pos, y)
    sprite.draw(layout, z=Layer.NOTE + y)


def draw_connector(
    sprite: Sprite,
    pos: LanePosition,
    y: float,
    prev_pos: LanePosition,
    prev_y: float,
):
    if prev_y < Layout.min_safe_y and y < Layout.min_safe_y:
        return
    if prev_y > Layout.lane_height and y > Layout.lane_height:
        return
    layout = connector_layout(
        pos=pos,
        y=y,
        prev_pos=prev_pos,
        prev_y=prev_y,
    )
    sprite.draw(layout, z=Layer.CONNECTOR + max(y, prev_y))


def play_hit_effects(
    note_particle: Particle,
    pos: LanePosition,
    judgment: Judgment,
):
    play_hit_sfx(judgment)
    play_hit_particle(note_particle, pos)


def play_hit_sfx(judgment: Judgment):
    match judgment:
        case Judgment.PERFECT:
            Effects.perfect.play(SFX_DISTANCE)
        case Judgment.GREAT:
            Effects.great.play(SFX_DISTANCE)
        case Judgment.GOOD:
            Effects.good.play(SFX_DISTANCE)


def play_hit_particle(
    note_particle: Particle,
    pos: LanePosition,
):
    note_particle.spawn(
        note_particle_layout(pos, scale=0.6),
        duration=0.5,
    )
    Particles.lane.spawn(
        lane_layout(pos),
        duration=0.2,
    )


def spawn_hold_particle(
    hold_particle: Particle,
    pos: LanePosition,
) -> ParticleHandle:
    return hold_particle.spawn(
        note_particle_layout(pos, scale=0.4),
        duration=1.0,
        loop=True,
    )


def move_hold_particle(
    handle: ParticleHandle,
    pos: LanePosition,
):
    handle.move(note_particle_layout(pos, scale=0.4))
