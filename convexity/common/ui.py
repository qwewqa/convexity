from sonolus.script.ui import UiConfig, UiJudgmentErrorPlacement, UiJudgmentErrorStyle

ui_config = UiConfig(
    judgment_error_style=UiJudgmentErrorStyle.ARROW_DOWN,
    judgment_error_placement=UiJudgmentErrorPlacement.BOTH,
    judgment_error_min=20.0,
)
