from sonolus.script.engine import TutorialMode

from convexity.common.effect import Effects
from convexity.common.particle import Particles
from convexity.common.skin import Skin
from convexity.tutorial.init import preprocess
from convexity.tutorial.instructions import InstructionIcons, Instructions
from convexity.tutorial.navigate import navigate
from convexity.tutorial.update import update

tutorial_mode = TutorialMode(
    skin=Skin,
    effects=Effects,
    particles=Particles,
    instructions=Instructions,
    instruction_icons=InstructionIcons,
    preprocess=preprocess,
    navigate=navigate,
    update=update,
)
