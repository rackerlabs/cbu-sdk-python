class OperationFailed(RuntimeError):
    def __init__(self, op, report):
        message = '{0}: {1}:{2}'.format(op, report._diagnostics, report.errors)
        RuntimeError.__init__(self, message)


class BackupFailed(OperationFailed):
    def __init__(self, report):
        OperationFailed.__init__(self, 'Backup', report)


class RestoreFailed(Exception):
    def __init__(self, report):
        OperationFailed.__init__(self, 'Restore', report)


class InconsistentInclusionsError(ValueError):
    def __init__(self, diff_set):
        msg_template = '{0} are included and excluded. Which did you mean?'
        ValueError.__init__(msg_template.format(diff_set))
