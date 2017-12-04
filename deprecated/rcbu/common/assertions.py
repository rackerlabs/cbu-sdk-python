def assert_is_none(name, value):
    """A convenience function for reporting on values that should be None.
    Raises a ValueError."""
    if value is not None:
        template = '{0} should be None, not {1}'
        raise ValueError(template.format(name, value))


def assert_bounded(name, lower, upper, value):
    """A convenience function for handling and reporting errors
    on bounded arguments. Raises a ValueError."""
    if value < lower or value > upper:
        template = '{0} {1} out of bounds [{2} - {3}]'
        raise ValueError(template.format(name, value, lower, upper))
