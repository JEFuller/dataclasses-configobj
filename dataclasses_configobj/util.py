import typing_inspect

def list_type(listT):
    """Get the T for a List[T]"""
    return typing_inspect.get_args(listT.annotation)[0]