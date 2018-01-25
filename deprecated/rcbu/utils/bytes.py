"""Utilities for handling byte quantities and strings."""


def dehumanize_bytes(human_bytes):
    """Convert a string in the format '2.23 GB' -> 2.23 * 10**30"""
    packed = human_bytes.split()
    amount, magnitude = packed[0], None
    if len(packed) == 2:
        magnitude = packed[1].upper()
    prefixes = ['YB', 'ZB', 'EB', 'PB', 'TB', 'GB', 'MB', 'KB']
    multipliers = [2**(i*10) for i in range(8, 0, -1)]
    magnitude_to_multiplier = {ma: mult for ma, mult in
                               zip(prefixes, multipliers)}
    multiplier = magnitude_to_multiplier.get(magnitude, 1)
    return int(float(amount) * multiplier)
