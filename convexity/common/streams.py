from sonolus.script.containers import VarArray
from sonolus.script.stream import Stream, StreamGroup, streams


@streams
class Streams:
    empty_touch_lanes: Stream[VarArray[float, 16]]
    note_touch_tracking: StreamGroup[float, 999999]
