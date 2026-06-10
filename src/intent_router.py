from dataclasses import dataclass, field

WORKFLOW_KEYWORDS = {
    "pose": [
        "pose", "posture", "standing", "sitting", "walking", "running",
        "pose reference", "copy pose", "same pose as", "match pose",
        "body position", "dancing", "jumping", "arms up",
    ],
    "upscale": [
        "upscale", "enhance resolution", "higher resolution",
        "4k", "8k", "upscale to", "enlarge", "super resolution",
        "increase resolution", "hi-res", "high res",
    ],
}

DEFAULT_WORKFLOW = "outfit"


@dataclass
class IntentResult:
    workflow_type: str
    needs_second_image: bool
    second_image_label: str
    keywords_matched: list[str] = field(default_factory=list)


def detect_intent(prompt: str, has_pose_image: bool = False) -> IntentResult:
    prompt_lower = prompt.lower()

    if has_pose_image:
        return IntentResult(
            workflow_type="pose",
            needs_second_image=True,
            second_image_label="pose reference",
            keywords_matched=["pose image provided"],
        )

    scored = {}
    for wf_type, keywords in WORKFLOW_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in prompt_lower]
        if matches:
            scored[wf_type] = len(matches)

    if scored:
        best = max(scored, key=lambda k: scored[k])
        needs_second = best == "pose"
        return IntentResult(
            workflow_type=best,
            needs_second_image=needs_second,
            second_image_label="pose reference" if needs_second else "",
            keywords_matched=[k for k in WORKFLOW_KEYWORDS[best] if k in prompt_lower],
        )

    return IntentResult(
        workflow_type=DEFAULT_WORKFLOW,
        needs_second_image=False,
        second_image_label="",
        keywords_matched=[],
    )
