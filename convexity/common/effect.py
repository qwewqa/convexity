from sonolus.script.effect import StandardEffect, effects

SFX_DISTANCE = 0.02


@effects
class Effects:
    stage: StandardEffect.STAGE

    perfect: StandardEffect.PERFECT
    great: StandardEffect.GREAT
    good: StandardEffect.GOOD

    perfect_alt: StandardEffect.PERFECT_ALTERNATIVE
    great_alt: StandardEffect.GREAT_ALTERNATIVE
    good_alt: StandardEffect.GOOD_ALTERNATIVE

    hold: StandardEffect.HOLD
