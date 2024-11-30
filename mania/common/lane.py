from mania.common.effect import SFX_DISTANCE, Effects
from mania.common.layout import LanePosition, lane_layout
from mania.common.options import Options
from mania.common.particle import Particles


def play_lane_effects(pos: LanePosition):
    play_lane_sfx()
    play_lane_particle(pos)


def play_lane_sfx():
    if Options.sfx_enabled:
        Effects.stage.play(SFX_DISTANCE)


def play_lane_particle(pos: LanePosition):
    if Options.lane_effect_enabled:
        Particles.lane.spawn(
            lane_layout(pos),
            duration=0.2,
        )
