from sonolus.script.particle import StandardParticle, particles


@particles
class Particles:
    lane: StandardParticle.LANE_LINEAR

    tap_note: StandardParticle.NOTE_LINEAR_TAP_CYAN
    hold_note: StandardParticle.NOTE_LINEAR_TAP_GREEN

    hold: StandardParticle.NOTE_LINEAR_HOLD_GREEN
