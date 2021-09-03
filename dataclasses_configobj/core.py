from dataclasses import dataclass, field
from inspect import Parameter, signature
from typing import Optional, Type, TypeVar

import configobj
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

    @dataclass
    class Nodes:
        builtin: dict = field(default_factory= dict)
        classes: dict = field(default_factory=dict)
        nested: dict = field(default_factory=dict)
        many: Optional[Type] = None

        def add(self, p: Parameter):
            name = p.name
            annotation = p.annotation
            if name == '_many':
                if self.many:
                    raise Exception(f'Can only handle one List per section, but given {self.many} and {annotation}')
                self.many = util.list_type(p)
            elif util.is_builtin(annotation):
                self.builtin[name] = annotation
            elif not util.has_generic_parameters(annotation):
                self.classes[name] = annotation
            else:
                self.nested[name] = annotation

        def is_many(self, name: str):
            # Any node which isn't of another kind is assumed to be part one of 'many'
            return not any([nodes.get(name) for nodes in [self.builtin, self.classes, self.nested]])

    nodes = Nodes()
    for p in params:
        nodes.add(p)

    builtin = {name: klass_(attrs) for (name, attrs) in config if (klass_ := nodes.builtin.get( name ))}
    classes = {name: klass_(**attrs) for (name, attrs) in config if (klass_ := nodes.classes.get( name ))}
    manys = [nodes.many(**{'_name': name} | attrs) for (name, attrs) in config if nodes.many and nodes.is_many(name)]
    nested = {name: lift(klass_, section) for (name, section) in config if (klass_ := nodes.nested.get( name ))}

    return klass(**(builtin | classes | nested | ({ '_many': manys } if len(manys) > 0 else {})))
