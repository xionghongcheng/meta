#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible quick-start entrypoint."""

from __future__ import annotations

import sys

from examples.quick_start import quick_start


if __name__ == "__main__":
    print(
        "[compat] `quick_start.py` moved to `examples/quick_start.py`. "
        "This root file is kept for backward compatibility.",
        file=sys.stderr,
    )
    quick_start()
