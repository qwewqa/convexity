from convexity.common.effect import SFX_DISTANCE, Effects
from convexity.common.layout import LanePosition, Layer, lane_layout, line_layout, note_layout
from convexity.common.options import Options
from convexity.common.particle import Particles
from convexity.common.skin import Skin


def draw_lane(pos: LanePosition):
    if not Options.laneless:
        Skin.lane.draw(lane_layout(pos), z=Layer.LANE)
        if not Options.slot_judge_line:
            Skin.judgment_line.draw(line_layout(pos, 0), z=Layer.JUDGE_LINE)
    if Options.slot_judge_line:
        Skin.slot.draw(note_layout(pos, 0), z=Layer.SLOT)


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
