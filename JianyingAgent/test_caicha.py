#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible wrapper for the tea-project smoke test."""

from __future__ import annotations

import sys

from tests.smoke.test_caicha import main


if __name__ == "__main__":
    print(
        "[compat] `test_caicha.py` moved to `tests/smoke/test_caicha.py`. "
        "This root file is kept for backward compatibility.",
        file=sys.stderr,
    )
    main()
