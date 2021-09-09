from dataclasses import dataclass, field
from typing import Optional, Type, TypeVar, Union, get_type_hints

from configobj import ConfigObj, Section
from typing_inspect import get_args, get_origin

# Based on https://github.com/DiffSK/configobj/blob/v5.0.6//validate.py#L1250
TYPES = {
    str: 'string',
    int: 'integer'
}


def to_spec(klass: Type):
    root = ConfigObj(_inspec=True, raise_errors=True, file_error=True)

    for name, klass_ in get_type_hints(klass).items():
        _to_spec(name, klass_, root, 1, root)

    return root


def _to_spec(name: str, klass: Type, parent, depth, main) -> None:
    name = '__many__' if name == '_many' else name

    isOptional = get_origin(klass) == Union and get_args(klass)[1] == type(None)
    if isOptional or name == '__many__':
        klass = get_args(klass)[0] 

    paramType = TYPES.get(klass)

    if paramType is None: # not a built in (or optional) type
        section = Section(parent, depth, main)
        parent[name] = section

        params = {name_ : klass_ for name_, klass_ in get_type_hints(klass).items() if name_ != '_name' }
        for name_, klass_ in params.items():
            paramType_ = TYPES.get(klass_)
            if paramType_ is None:
                _to_spec(name_, klass_, section, depth+1, main)
            else:
                section.__setitem__(name_, paramType_)
        return

    # is a built in type
    parent.__setitem__(name, paramType + ('(default=None)' if isOptional else ''))

T = TypeVar('T')

def lift(klass: Type[T], configObject) -> T:
    params = get_type_hints(klass)
    config = configObject.items()

    @dataclass
    class Nodes:
        many: Optional[Type] = None
        scalars: dict = field(default_factory=dict)
        classes: dict = field(default_factory=dict)
        nested: dict = field(default_factory=dict)

        def add(self, name: str, klass_: Type):
            if name == '_many':
                if self.many:
                    raise Exception(f'Can only handle one List per section, but given {self.many} and {klass_}')
                self.many = get_args(klass_)[0]
            elif klass_.__module__ == 'builtins':
                self.scalars[name] = klass_
            elif get_origin(klass_) == Union and get_args(klass_)[1] == type(None):
                self.scalars[name] = get_args(klass_)[0]
            elif all([c.__module__ == 'builtins' for c in get_type_hints(klass_).values()]):
                self.classes[name] = klass_
            else:
                self.nested[name] = klass_

        def is_many(self, name: str):
            # Any node which isn't of another kind is assumed to be part one of 'many'
            return not any([nodes.get(name) for nodes in [self.scalars, self.classes, self.nested]])

    nodes = Nodes()
    for name, klass_ in params.items():
        nodes.add(name, klass_)

    builtin = {name: None if attrs is None else klass_(attrs) for (name, attrs) in config if (klass_ := nodes.scalars.get( name ))}
    classes = {name: klass_(**attrs) for (name, attrs) in config if (klass_ := nodes.classes.get( name ))}
    manys = [nodes.many(**{'_name': name} | attrs) for (name, attrs) in config if nodes.many and nodes.is_many(name)]
    nested = {name: lift(klass_, section) for (name, section) in config if (klass_ := nodes.nested.get( name ))}

    return klass(**(builtin | classes | nested | ({ '_many': manys } if len(manys) > 0 else {})))
