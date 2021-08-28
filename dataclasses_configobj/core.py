from inspect import signature
from typing import List

import configobj
import typing_inspect
from configobj import ConfigObj


def to_spec(sections):
    sections = [sections] if not isinstance(sections, List) else sections

    root = ConfigObj()
    _to_spec(sections, root, 1, root)
    return root


def _to_spec(sectionClasses, parent, depth, main):
    for sectionClass in sectionClasses:
        section = configobj.Section(parent, depth, main)

        origin = typing_inspect.get_origin(sectionClass)
        if origin == list:
            name = '__many__'
            isList = True
            sectionClass = typing_inspect.get_args(sectionClass)[0]
        elif origin == None:
            name = sectionClass.__name__
            isList = False
        else:
            raise Exception(f'Unsupported type: {origin}')

        parent[name] = section

        sig = signature(sectionClass)
        items = sig.parameters.items()
        for paramName, param in items:
            if isList and paramName == '_name':
                continue

            paramType = param.annotation.__name__

            if paramType == 'str':
                paramType = 'string'
            elif paramType == 'int':
                paramType = 'integer'
            else:
                raise Exception(f'Unsupported type: {name}')

            section.__setitem__(paramName, paramType)

    return parent
