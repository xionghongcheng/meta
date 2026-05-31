#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Allow `python -m apps` to invoke the CLI compatibility wrapper."""

from entrypoints.apps.cli import main


if __name__ == "__main__":
    main()
