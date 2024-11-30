from sonolus.script.effect import StandardEffect, effects

SFX_DISTANCE = 0.2


@effects
class Effects:
    stage: StandardEffect.STAGE

    perfect: StandardEffect.PERFECT
    great: StandardEffect.GREAT
    good: StandardEffect.GOOD

    hold: StandardEffect.HOLD
