from sonolus.script.effect import StandardEffect, effects

SFX_DISTANCE = 0.02


@effects
class Effects:
    stage: StandardEffect.STAGE

    perfect: StandardEffect.PERFECT
    great: StandardEffect.GREAT
    good: StandardEffect.GOOD

    hold: StandardEffect.HOLD
