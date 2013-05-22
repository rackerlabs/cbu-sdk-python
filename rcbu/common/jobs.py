BUSY_STATUS = ('InProgress', 'Queued', 'Preparing')
DONE_STATUS = ('Completed', 'CompletedWithErrors', 'Stopped',
               'Skipped', 'Failed', 'Missed')


def is_running(job):
    return job['Status'] in BUSY_STATUS
