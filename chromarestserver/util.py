# -*- coding: utf-8 -*-
"""Misc utilities and helpers module."""
import logging
import random
import time

logger = logging.getLogger()


def usleep_range(min_usec, max_usec):
    """Sleep randomly between min/max microseconds.

    Args:
        min_usec (int): minimum number of microseconds to sleep
        max_usec (int): maximum number of microseconds to sleep
    """
    sec = random.randint(min_usec, max_usec) / 1000000.0
    logger.debug('sleeping for sec="%s"', sec)
    time.sleep(sec)


def clamp(n, smallest, largest):
    """Ensure 'n' is no smaller or larger then a certain range.

    If the number is smaller than the range it will be returned as
    the smallest.

    If the number is larger than largest it will be returned as the
    largest.

    Args:
        n (int): integer to inspect
        smallest (int): no smaller than this is allowed
        largest (int): no larger than this is allowed

    Returns:
        int: the "clamped" input
    """
    return max(smallest, min(n, largest))


def clamp255(n):
    """Ensure a number is between 0-255 (inclusive).

    Args:
        n (int): integer to inspect

    Returns:
        int: the "clamped" input
    """
    return clamp(n, 0, 255)
