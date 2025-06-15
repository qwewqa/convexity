from sonolus.script.containers import VarArray
from sonolus.script.stream import Stream, streams


@streams
class Streams:
    empty_touch_lanes: Stream[VarArray[float, 16]]
