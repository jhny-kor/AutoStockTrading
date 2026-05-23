"""Output helpers for command-line scripts."""

from __future__ import annotations

import sys
from typing import TextIO


def _reconfigure_utf8(stream: TextIO) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="replace")
    except ValueError:
        return


def configure_utf8_stdio() -> None:
    """Force UTF-8 output for tools launched under sparse locales."""
    _reconfigure_utf8(sys.stdout)
    _reconfigure_utf8(sys.stderr)
