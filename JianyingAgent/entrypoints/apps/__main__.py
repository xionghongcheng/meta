#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Allow `python -m entrypoints.apps` to invoke the unified CLI."""

from .cli import main


if __name__ == "__main__":
    main()
