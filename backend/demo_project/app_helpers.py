"""Tiny utility module added so the demo report can illustrate a real import edge."""


def normalize_label(value: str) -> str:
    """Normalize a display label without mutating the incoming value."""
    return " ".join(value.split())[:80]
