from sonolus.script.engine import PreviewMode

from convexity.common.skin import Skin
from convexity.preview.bar import BpmChange
from convexity.preview.init import Init
from convexity.preview.lane import Lane
from convexity.preview.note import Note, UnscoredNote
from convexity.preview.stage import Stage

preview_mode = PreviewMode(
    archetypes=[
        Init,
        Stage,
        Lane,
        Note,
        UnscoredNote,
        BpmChange,
    ],
    skin=Skin,
)
