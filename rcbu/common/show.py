class Show(object):
    def __repr__(self):
        return '{0}({1})'.format(self.__class__, self.__dict__)
