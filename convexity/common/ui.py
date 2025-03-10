from sonolus.script.ui import UiConfig, UiJudgmentErrorPlacement, UiJudgmentErrorStyle

ui_config = UiConfig(
    judgment_error_style=UiJudgmentErrorStyle.LATE,
    judgment_error_placement=UiJudgmentErrorPlacement.TOP,
    judgment_error_min=20.0,
)
