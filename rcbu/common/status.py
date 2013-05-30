_int_to_status = {
    0: 'Creating',
    1: 'Queued',
    2: 'InProgress',
    3: 'Completed',
    4: 'Stopped',
    5: 'Failed',
    6: 'StartRequested',
    7: 'StopRequested',
    8: 'CompletedWithErrors',
    9: 'Preparing'
}

BUSY_STATUS = ('StartRequested', 'Creating', 'InProgress',
               'StopRequested', 'Queued', 'Preparing')
DONE_STATUS = ('Completed', 'CompletedWithErrors', 'Stopped',
               'Skipped', 'Failed', 'Missed')

int_to_status = lambda n: _int_to_status[n]


def busy(status):
    return status in BUSY_STATUS
