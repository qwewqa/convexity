from sonolus.script.particle import StandardParticle, particles


@particles
class Particles:
    lane: StandardParticle.LANE_LINEAR

    tap_note: StandardParticle.NOTE_LINEAR_TAP_CYAN
    hold_note: StandardParticle.NOTE_LINEAR_TAP_GREEN

    flick_note: StandardParticle.NOTE_LINEAR_ALTERNATIVE_RED
    right_flick_note: StandardParticle.NOTE_LINEAR_ALTERNATIVE_YELLOW
    left_flick_note: StandardParticle.NOTE_LINEAR_ALTERNATIVE_PURPLE

    swing_note: StandardParticle.NOTE_LINEAR_TAP_CYAN

    hold: StandardParticle.NOTE_LINEAR_HOLD_GREEN
