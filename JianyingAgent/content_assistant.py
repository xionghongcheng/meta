#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible topic CLI entrypoint."""

from __future__ import annotations

import sys

from entrypoints.apps.topic_cli import main


if __name__ == "__main__":
    print(
        "[compat] `content_assistant.py` is kept for backward compatibility. "
        "Prefer `python -m apps suggest ...` or `python -m apps profile ...`.",
        file=sys.stderr,
    )
    main()
