from inspect import signature
import typing_inspect

def list_type(listT):
    """Get the T for a List[T]"""
    return typing_inspect.get_args(listT.annotation)[0]

def is_builtin(klass):
    return klass.__module__ == 'builtins'

def has_generic_parameters(klass):
    if is_builtin(klass):
        return False
    else:
        parameters = signature(klass).parameters.values()
        return any([typing_inspect.get_origin(p.annotation) for p in parameters])
