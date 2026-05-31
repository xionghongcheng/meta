#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible wrapper for the dad-VR smoke test."""

from __future__ import annotations

import sys

from tests.smoke.test_dad_buddha import main


if __name__ == "__main__":
    print(
        "[compat] `test_dad Buddha.py` moved to `tests/smoke/test_dad_buddha.py`. "
        "This root file is kept for backward compatibility.",
        file=sys.stderr,
    )
    main()
