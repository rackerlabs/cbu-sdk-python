from rcbu.common.assertions import assert_bounded


def seconds(time):
    '''Given %H:%M:%S -> seconds. Hours can be arbitrarily large.'''
    try:
        hours, minutes, seconds = [int(f) for f in time.split(':')]
    except ValueError:
        msg = 'expecting format %H:%M:%S, not {0}'.format(time)
        raise ValueError(msg)

    assert_bounded('minutes', 0, 59, minutes)
    assert_bounded('seconds', 0, 59, seconds)
    return hours * 3600 + minutes * 60 + seconds


def tuple(seconds):
    '''Returns (hours, minutes, seconds) from seconds.'''
    return (seconds // 3600,
            (seconds // 60) - ((seconds // 3600) * 60),
            seconds % 60)
