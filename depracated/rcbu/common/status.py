from rcbu.common.http import Http


int_to_status = lambda n: {
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
}[n]

BUSY_STATUS = ('StartRequested', 'Creating', 'InProgress',
               'StopRequested', 'Queued', 'Preparing')
DONE_STATUS = ('Completed', 'CompletedWithErrors', 'Stopped',
               'Skipped', 'Failed', 'Missed')


def busy(status):
    return status in BUSY_STATUS


_state_interpret = {
    'restore': lambda r: int_to_status(r.json()['RestoreStateId']),
    'backup': lambda r: r.json()['CurrentState']
}


class Status(object):
    def __init__(self, command_id, command_type, connection):
        self._id = command_id
        self._type = command_type
        self._connection = connection

    @property
    def id(self):
        return self._id

    @property
    def state(self):
        url = '{0}/{1}/{2}'.format(self._connection.host,
                                   self._type, self.id)
        resp = self._connection.request(Http.get, url)
        return _state_interpret[self._type](resp)
