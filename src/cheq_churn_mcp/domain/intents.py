"""Reviewed reason-intent taxonomy and natural-language aliases."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReasonIntent:
    """A versioned, reviewable semantic category for controlled reason values."""

    values: tuple[str, ...]
    definition: str


REASON_INTENTS: dict[str, ReasonIntent] = {
    "unclear_reason": ReasonIntent(
        values=("Don't know",),
        definition=(
            "Source churn-reason label 'Don't know'. This dataset stores a controlled label, "
            "not free-text responses, so no embedding or semantic search is required."
        ),
    )
}
