#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Allow `python -m webui` to invoke the web UI compatibility wrapper."""

from entrypoints.webui.server import main


if __name__ == "__main__":
    main()
