from sonolus.script.particle import StandardParticle, particles


@particles
class Particles:
    lane: StandardParticle.LANE_LINEAR

    tap_linear: StandardParticle.NOTE_LINEAR_TAP_CYAN
    hold_linear: StandardParticle.NOTE_LINEAR_TAP_GREEN

    flick_linear: StandardParticle.NOTE_LINEAR_ALTERNATIVE_RED
    right_flick_linear: StandardParticle.NOTE_LINEAR_ALTERNATIVE_YELLOW
    left_flick_linear: StandardParticle.NOTE_LINEAR_ALTERNATIVE_PURPLE

    swing_linear: StandardParticle.NOTE_LINEAR_TAP_CYAN

    hold_active_linear: StandardParticle.NOTE_LINEAR_HOLD_GREEN

    tap_circular: StandardParticle.NOTE_CIRCULAR_TAP_CYAN
    hold_circular: StandardParticle.NOTE_CIRCULAR_TAP_GREEN

    flick_circular: StandardParticle.NOTE_CIRCULAR_ALTERNATIVE_RED
    right_flick_circular: StandardParticle.NOTE_CIRCULAR_ALTERNATIVE_YELLOW
    left_flick_circular: StandardParticle.NOTE_CIRCULAR_ALTERNATIVE_PURPLE

    swing_circular: StandardParticle.NOTE_CIRCULAR_TAP_CYAN

    hold_active_circular: StandardParticle.NOTE_CIRCULAR_HOLD_GREEN
