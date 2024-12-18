from sonolus.script.instruction import (
    StandardInstruction,
    StandardInstructionIcon,
    instruction_icons,
    instructions,
)


@instructions
class Instructions:
    tap: StandardInstruction.TAP
    tap_flick: StandardInstruction.TAP_FLICK
    hold: StandardInstruction.HOLD_FOLLOW
    release: StandardInstruction.RELEASE
    hold_flick: StandardInstruction.FLICK
    slide: StandardInstruction.SLIDE


@instruction_icons
class InstructionIcons:
    hand: StandardInstructionIcon.HAND
