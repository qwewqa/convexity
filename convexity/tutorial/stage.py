from sonolus.script.array import Array

from convexity.common.lane import draw_lane
from convexity.common.layout import lane_to_pos
from convexity.common.stage import draw_stage


def draw_tutorial_stage():
    for lane in Array(-2, -1, 0, 1, 2):
        draw_lane(lane_to_pos(lane))
    draw_stage(lane_to_pos(0, 5))
