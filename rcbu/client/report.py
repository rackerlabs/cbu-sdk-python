class Report(object):
    def __init__(self, report_id):
        self.report_id = report_id

    @property
    def ok(self):
        pass

    @property
    def errors(self):
        pass

    @property
    def id(self):
        return self.report_id

    @property
    def duration(self):
        pass

    def get_configuration(self):
        pass
