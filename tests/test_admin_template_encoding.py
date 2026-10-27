"""Regression tests for admin template character encoding."""

from pathlib import Path


ADMIN_BASE = Path(__file__).resolve().parents[1] / "templates" / "admin_base.html"


def test_admin_base_template_has_no_mojibake():
    text = ADMIN_BASE.read_text(encoding="utf-8")

    # The corrupted template previously contained UTF-8 bytes that had been
    # decoded as Windows-1252 and re-encoded as UTF-8.
    assert "\u00e2" not in text


def test_admin_base_template_contains_intended_icons():
    text = ADMIN_BASE.read_text(encoding="utf-8")

    intended = [
        "\u2022",  # bullet
        "\u25a6",  # squared square
        "\u2713",  # check mark
        "\u25a4",  # square with horizontal fill
        "\u2659",  # white chess pawn
        "\u25c9",  # fisheye
        "\u25c7",  # white diamond
        "\u2699",  # gear
        "\u2b05",  # leftwards black arrow
        "\u2630",  # trigram for heaven
        "\u21aa",  # rightwards arrow with hook
        "\u2191",  # upwards arrow
        "\u27a1",  # black rightwards arrow
        "\u2715",  # multiplication x
    ]

    for character in intended:
        assert character in text, f"Missing intended character: {character!r}"