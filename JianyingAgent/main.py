#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible roughcut CLI entrypoint."""

from __future__ import annotations

import sys

from entrypoints.apps.roughcut_cli import main


if __name__ == "__main__":
    print(
        "[compat] `main.py` is kept for backward compatibility. "
        "Prefer `python -m apps roughcut ...`.",
        file=sys.stderr,
    )
    main()
