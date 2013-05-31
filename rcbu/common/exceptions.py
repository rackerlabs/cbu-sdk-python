class BackupFailed(Exception):
    def __init__(self, report):
        self.message = '{0}:{1}'.format(report._diagnostics, report.errors)


class RestoreFailed(Exception):
    def __init__(self, report):
        self.message = '{0}:{1}'.format(report._diagnostics, report.errors)
