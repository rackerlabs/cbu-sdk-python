class DisconnectedError(RuntimeError):
    def __init__(self):
        msg = 'Must self.connect before continuing.'
        RuntimeError.__init__(self, msg)


class OperationFailed(RuntimeError):
    def __init__(self, op, report):
        message = '{0}: {1}:{2}'.format(op, report._diagnostics, report.errors)
        RuntimeError.__init__(self, message)


class BackupFailed(OperationFailed):
    def __init__(self, report):
        OperationFailed.__init__(self, 'Backup', report)


class RestoreFailed(OperationFailed):
    def __init__(self, report):
        OperationFailed.__init__(self, 'Restore', report)


class InconsistentInclusionsError(ValueError):
    def __init__(self, diff_set):
        msg_template = '{0} are included and excluded. Which did you mean?'
        ValueError.__init__(self, msg_template.format(diff_set))


class NoEndpointFound(RuntimeError):
    def __init__(self, username, region):
        msg = 'No endpoint found for user {0} in region {1}'
        super(NoEndpointFound, self).__init__(msg.format(username, region))
