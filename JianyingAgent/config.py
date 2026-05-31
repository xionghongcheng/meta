#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible config module.

Prefer importing `infra.config.Config` in new code.
"""

from infra.config import Config

__all__ = ["Config"]
