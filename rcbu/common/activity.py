import rcbu.utils.date as date


def _args_from_dict(body):
    return {
        '_id': body['ID'],
        '_type': body['Type'],
        '_parent_id': body['ParentId'],
        '_name': body['DisplayName'],
        '_deleted': body['IsBackupConfigurationDeleted'],
        '_source': {
            'agent_id': body['SourceMachineAgentId'],
            'name': body['SourceMachineName']
        },
        '_destination': {
            'agent_id': body['DestinationMachineAgentId'],
            'name': body['DestinationMachineName']
        },
        '_state': body['CurrentState'],
        '_time': body['TimeOfActivity']
    }


def from_dict(body):
    args = _args_from_dict(body)
    return Activity(**args)


class Activity(object):
    def __init__(self, **kwargs):
        [setattr(self, k, v) for k, v in kwargs.items()]

    def __repr__(self):
        form = ('<{0}Activity id:{1} name:{2} state:{3} time:{4}>')
        pretty_type = self.type[0].upper() + self.type[1:].lower()
        return form.format(pretty_type, self.id, self.name, self.state,
                           self.time.isoformat())

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type

    @property
    def parent(self):
        return self._parent_id

    @property
    def name(self):
        return self._name

    @property
    def deleted(self):
        return self._deleted

    @property
    def source(self):
        src = self._source
        return '{0} {1}'.format(src['name'], src['agent_id'])

    @property
    def destination(self):
        if self.type.lower() == 'restore':
            dst = self._destination
            return '{0} {1}'.format(dst['name'], dst['agent_id'])
        return None

    @property
    def state(self):
        return self._state

    @property
    def time(self):
        return date.parse(self._time)
