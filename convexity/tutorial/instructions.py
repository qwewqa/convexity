from sonolus.script.instruction import (
    StandardInstruction,
    StandardInstructionIcon,
    instruction_icons,
    instructions,
)


@instructions
class Instructions:
    tap: StandardInstruction.TAP


@instruction_icons
class InstructionIcons:
    hand: StandardInstructionIcon.HAND
