from inspect import signature
from typing import List, Literal, Type, TypeVar

import configobj
import typing_inspect
from configobj import ConfigObj

import dataclasses_configobj.util as util

# Based on https://github.com/DiffSK/configobj/blob/v5.0.6//validate.py#L1250
TYPES = {
    str: 'string',
    int: 'integer'
}



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
        paramType = TYPES.get(param.annotation)
        if paramType is None:
            _to_spec(param, section, depth+1, main)
        else:
            section.__setitem__(paramName, paramType)

    return parent

T = TypeVar('T')

def lift(klass: Type[T], configObject) -> T:
    params = list(signature(klass).parameters.values())
    config = configObject.items()

    notMany = [p for p in params if p.name != '_many']
    leafsBuiltin = {p.name: p.annotation for p in notMany if util.is_builtin(p.annotation)}
    leafsClass = {p.name: p.annotation for p in notMany if not util.is_builtin(p.annotation) and not util.has_generic_parameters(p.annotation)}
    nested = { p.name: p.annotation for p in params if util.has_generic_parameters(p.annotation) }
    manys = [ util.list_type(p) for p in params if p.name == '_many'  ]

    leafBuiltinMatches = {name: klass_(attrs) for (name, attrs) in config if (klass_ := leafsBuiltin.get( name ))}
    leafClassMatches = {name: klass_(**attrs) for (name, attrs) in config if (klass_ := leafsClass.get( name ))}

    if len(manys) > 1:
        raise Exception(f'Can only handle one list per section, but given {manys}')
    elif len(manys) == 1:
        manyClass = manys[0]
        manyMatches = [manyClass(**{'_name': name} | attrs) for (name, attrs) in config if not leafsBuiltin.get( name ) and not leafsClass.get( name )]
    else:
        manyMatches = []

    nestedMatches = {name: lift(klass_, section) for (name, section) in config if (klass_ := nested.get( name ))}

    return klass(**(leafBuiltinMatches | leafClassMatches | nestedMatches | ({ '_many': manyMatches } if len(manyMatches) > 0 else {})))