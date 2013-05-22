BUSY_STATUS = ('InProgress', 'Queued', 'Preparing')
DONE_STATUS = ('Completed', 'CompletedWithErrors', 'Stopped',
               'Skipped', 'Failed', 'Missed')


def is_running(job):
    return job['CurrentState'] in BUSY_STATUS
