from mania.common.effect import SFX_DISTANCE, Effects
from mania.common.layout import LanePosition, Layer, lane_layout, line_layout
from mania.common.options import Options
from mania.common.particle import Particles
from mania.common.skin import Skin


def draw_lane(pos: LanePosition):
    Skin.lane.draw(lane_layout(pos), z=Layer.LANE)
    # Skin.slot.draw(note_layout(pos, 0), z=Layer.SLOT)
    Skin.judgment_line.draw(line_layout(pos, 0), z=Layer.JUDGE_LINE)


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
