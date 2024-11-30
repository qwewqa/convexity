from sonolus.script.engine import TutorialMode

from mania.common.effect import Effects
from mania.common.particle import Particles
from mania.common.skin import Skin
from mania.tutorial.init import preprocess
from mania.tutorial.instructions import InstructionIcons, Instructions
from mania.tutorial.navigate import navigate
from mania.tutorial.update import update

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
