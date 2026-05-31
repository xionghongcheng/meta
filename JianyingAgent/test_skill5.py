#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible wrapper for the exporter smoke test."""

from __future__ import annotations

import sys

from tests.smoke.test_skill5_exporter import test_create_draft


if __name__ == "__main__":
    print(
        "[compat] `test_skill5.py` moved to `tests/smoke/test_skill5_exporter.py`. "
        "This root file is kept for backward compatibility.",
        file=sys.stderr,
    )
    test_create_draft()
