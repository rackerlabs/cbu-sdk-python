import enum


_methods = 'head get put post delete patch options'.split()
Http = enum.Enum('Http', _methods)
_etr = {k: v for k, v in zip(Http, _methods)}


def enum_to_method(http_enum_value):
    return _etr[http_enum_value]
