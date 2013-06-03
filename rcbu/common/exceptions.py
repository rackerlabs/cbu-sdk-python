class BackupFailed(Exception):
    def __init__(self, report):
        self.message = '{0}:{1}'.format(report._diagnostics, report.errors)


class RestoreFailed(Exception):
    def __init__(self, report):
        self.message = '{0}:{1}'.format(report._diagnostics, report.errors)


class InconsistentInclusionsError(Exception):
    def __init__(self, diff_set):
        msg_template = '{0} are included and excluded. Which did you mean?'
        self.message = msg_template.format(diff_set)
