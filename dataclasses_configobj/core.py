from dataclasses import dataclass, field
from typing import Optional, Type, TypeVar, get_type_hints


import configobj
from configobj import ConfigObj, Section

import dataclasses_configobj.util as util

# Based on https://github.com/DiffSK/configobj/blob/v5.0.6//validate.py#L1250
TYPES = {
    str: 'string',
    int: 'integer'
}


def to_spec(klass: Type):
    root = ConfigObj()

    for name, klass_ in get_type_hints(klass).items():
        _to_spec(name, klass_, root, 1, root)

    return root

def _to_spec(name: str, klass: Type, parent, depth, main):
    name = '__many__' if name == '_many' else name
    section = Section(parent, depth, main)
    parent[name] = section

    paramType = TYPES.get(klass)
    isSection = paramType is None # i.e. not a built in type

    if isSection:
        klass = util.list_type(klass) if name == '__many__' else klass
        params = {name_ : klass_ for name_, klass_ in get_type_hints(klass).items() if name_ != '_name' }
        for name_, klass_ in params.items():
            paramType_ = TYPES.get(klass_)
            if paramType_ is None:
                _to_spec(name_, klass_, section, depth+1, main)
            else:
                section.__setitem__(name_, paramType_)

    else:
        parent.__setitem__(name, paramType)

        areNested = [isinstance(parent.get(s), Section) for s in parent.sections]
        if any(areNested):
            ourIdx = parent.sections.index(name)
            firstNestedIdx = areNested.index(True)

            if ourIdx > firstNestedIdx:
                parent.sections.insert(firstNestedIdx, parent.sections.pop(ourIdx))

    return parent

T = TypeVar('T')

def lift(klass: Type[T], configObject) -> T:
    params = get_type_hints(klass)
    config = configObject.items()

    @dataclass
    class Nodes:
        builtin: dict = field(default_factory= dict)
        classes: dict = field(default_factory=dict)
        nested: dict = field(default_factory=dict)
        many: Optional[Type] = None

        def add(self, name: str, klass_: Type):
            if name == '_many':
                if self.many:
                    raise Exception(f'Can only handle one List per section, but given {self.many} and {klass_}')
                self.many = util.list_type(klass_)
            elif util.is_builtin(klass_):
                self.builtin[name] = klass_
            elif not util.has_generic_parameters(klass_):
                self.classes[name] = klass_
            else:
                self.nested[name] = klass_

        def is_many(self, name: str):
            # Any node which isn't of another kind is assumed to be part one of 'many'
            return not any([nodes.get(name) for nodes in [self.builtin, self.classes, self.nested]])

    nodes = Nodes()
    for name, klass_ in params.items():
        nodes.add(name, klass_)

    builtin = {name: klass_(attrs) for (name, attrs) in config if (klass_ := nodes.builtin.get( name ))}
    classes = {name: klass_(**attrs) for (name, attrs) in config if (klass_ := nodes.classes.get( name ))}
    manys = [nodes.many(**{'_name': name} | attrs) for (name, attrs) in config if nodes.many and nodes.is_many(name)]
    nested = {name: lift(klass_, section) for (name, section) in config if (klass_ := nodes.nested.get( name ))}

    return klass(**(builtin | classes | nested | ({ '_many': manys } if len(manys) > 0 else {})))
