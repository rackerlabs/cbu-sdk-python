class Restore(object):
    def __init__(self, backup_id):
        self.backup_id = backup_id

    @property
    def running(self):
        pass

    @property
    def progress(self):
        pass

    @property
    def state(self):
        pass

    @property
    def inclusions(self):
        pass

    @property
    def exclusions(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def report(self):
        pass
