from sonolus.script.instruction import clear_instruction
from sonolus.script.runtime import time

from convexity.tutorial.phases import TutorialState, tutorial_phases
from convexity.tutorial.stage import draw_tutorial_stage


def update():
    if TutorialState.phase_start_time == 0:
        TutorialState.phase_start_time = time()
    draw_tutorial_stage()
    if TutorialState.phase_update:
        TutorialState.phase_update = False
        TutorialState.phase_start_time = time()
        clear_instruction()
    for i, phase in enumerate(tutorial_phases):
        if i != TutorialState.tutorial_phase:
            continue
        if not phase():
            TutorialState.tutorial_phase += 1
            TutorialState.tutorial_phase %= len(tutorial_phases)
            TutorialState.phase_update = True
        break
