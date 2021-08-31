from inspect import signature
from typing import List, Type, TypeVar

import configobj
import typing_inspect
from configobj import ConfigObj

import dataclasses_configobj.util as util


def to_spec(klass):
    root = ConfigObj()

    classParams = signature(klass).parameters.values()
    for classParam in classParams:
        _to_spec(classParam, root, 1, root)

    return root

def _to_spec(classParam, parent, depth, main):
    name = '__many__' if classParam.name == '_many' else classParam.name
    section = configobj.Section(parent, depth, main)
    parent[name] = section

    klass = util.list_type(classParam) if classParam.name == '_many' else classParam.annotation 
    params = [p for p in signature(klass).parameters.items() if p[0] != '_name']

    for paramName, param in params:
        # Based on https://github.com/DiffSK/configobj/blob/v5.0.6//validate.py#L1250
        types = {
            str: 'string',
            int: 'integer'
        }

        paramType = types.get(param.annotation)
        if paramType is None:
            _to_spec(param, section, depth+1, main)
        else:
            section.__setitem__(paramName, paramType)

    return parent

T = TypeVar('T')

def lift(klass: Type[T], configObject) -> T:
    params = list(signature(klass).parameters.values())
    config = configObject.items()

    # explicit are those which are not _many
    explicitClasses = {name: p.annotation for p in params if (name := p.name) != '_many'}
    explicitMatches = {name: klass_(**attrs) for (name, attrs) in config if (klass_ := explicitClasses.get( name ))}

    manyClasses = [ util.list_type(p) for p in params if p.name == '_many'  ]

    if len (manyClasses) == 0:
        return klass(**explicitMatches)
    elif len (manyClasses) > 1:
        raise Exception(f'Can only handle one list per section, but given {manyClasses}')
    else:
        manyClass = manyClasses[0]
        rest = [manyClass(**{'_name': name} | attrs) for (name, attrs) in config if not explicitClasses.get( name )]
        return klass(**(explicitMatches | { '_many': rest }))
