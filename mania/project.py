from sonolus.script.engine import Engine, EngineData
from sonolus.script.project import Project

from mania.common.options import Options
from mania.common.ui import ui_config
from mania.level import levels
from mania.play.mode import play_mode
from mania.preview.mode import preview_mode
from mania.tutorial.mode import tutorial_mode
from mania.watch.mode import watch_mode

engine = Engine(
    name="mania",
    title="Mania",
    skin="pixel",
    particle="pixel",
    background="vanilla",
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
