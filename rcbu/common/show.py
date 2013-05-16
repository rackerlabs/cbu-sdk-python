class Show(object):
    def __repr__(self):
        return '{}({})'.format(self.__class__, self.__dict__)
