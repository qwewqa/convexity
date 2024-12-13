from sonolus.script.engine import Engine, EngineData
from sonolus.script.project import Project

from convexity.common.options import Options
from convexity.common.ui import ui_config
from convexity.level import levels
from convexity.play.mode import play_mode
from convexity.preview.mode import preview_mode
from convexity.tutorial.mode import tutorial_mode
from convexity.watch.mode import watch_mode

engine = Engine(
    name="convexity",
    title="Convexity",
    skin="pixel",
    particle="pixel",
    effect="8bit",
    background="darkblue",
    data=EngineData(
        ui=ui_config,
        options=Options,
        play=play_mode,
        watch=watch_mode,
        preview=preview_mode,
        tutorial=tutorial_mode,
    ),
)

project = Project(
    engine=engine,
    levels=levels,
)
