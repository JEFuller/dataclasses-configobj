from typing import List, Type, get_type_hints

from typing_inspect import get_args, get_origin

def list_type(listT: List):
    """Get the T for a List[T]"""
    return get_args(listT)[0]

def is_builtin(klass: Type):
    return klass.__module__ == 'builtins'

def has_generic_parameters(klass: Type):
    if is_builtin(klass):
        return False
    else:
        classes = get_type_hints(klass).values()
        return any([get_origin(c) for c in classes])
