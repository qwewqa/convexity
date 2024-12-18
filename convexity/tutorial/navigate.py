from sonolus.script.runtime import navigation_direction

from convexity.tutorial.phases import TutorialState, tutorial_phases


def navigate():
    TutorialState.tutorial_phase += navigation_direction() + len(tutorial_phases)
    TutorialState.tutorial_phase %= len(tutorial_phases)
    TutorialState.phase_update = True
