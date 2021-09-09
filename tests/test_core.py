import unittest
from dataclasses import dataclass
from typing import List, Optional, Type, TypeVar

import configobj
import validate
from dataclasses_configobj import core


class CoreTestCase(unittest.TestCase):
    def test_config(self):
        spec = list(map(str.strip, """\
        [foo]
        bar = string
        pip = integer\
        """.split('\n')))

        infile = list(map(str.strip, """\
        [foo]
        bar = one
        pip = 1\
        """.split('\n')))

        root = configobj.ConfigObj(infile=infile, configspec=spec)
        vtor = validate.Validator()
        res = root.validate(vtor, preserve_errors=True)
        self.assertEqual(res, True)

        foo = root['foo']
        self.assertIsNotNone(foo)
        self.assertEqual(foo['bar'], 'one')
        self.assertEqual(foo['pip'], 1)

    def test_to_spec_1(self):

        @dataclass
        class Foo:
            bar: str
            pip: int

        @dataclass
        class Config:
            foo: Foo

        expectedSpec = list(map(str.strip, """\
        [foo]
        bar = string
        pip = integer\
        """.split('\n')))

        root = configobj.ConfigObj()
        foo = configobj.Section(root, 1, root)
        root['foo'] = foo
        foo.__setitem__('bar', 'string')
        foo.__setitem__('pip', 'integer')
        self.assertEqual(expectedSpec, root.write())

        spec = core.to_spec(Config)
        self.assertEqual(expectedSpec, spec.write())

    def test_to_spec_2(self):

        @dataclass
        class Foo:
            a: str

        @dataclass
        class Bar:
            b: int

        @dataclass
        class Config:
            pip: str
            foo: Foo
            bar: Bar
            baz: str

        expectedSpec = list(map(str.strip, """\
        pip = string
        baz = string
        [foo]
        a = string
        [bar]
        b = integer\
        """.split('\n')))

        root = configobj.ConfigObj()
        root['pip'] = 'string'
        root['baz'] = 'string'
        foo = configobj.Section(root, 1, root)
        root['foo'] = foo
        foo.__setitem__('a', 'string')
        bar = configobj.Section(root, 1, root)
        root['bar'] = bar
        bar.__setitem__('b', 'integer')
        self.assertEqual(expectedSpec, root.write())

        spec = core.to_spec(Config)
        self.assertEqual(expectedSpec, spec.write())

    def test_to_spec_3(self):

        @dataclass
        class Single:
            other: str

        @dataclass
        class OneOfMany:
            _name: str
            val: str

        @dataclass
        class Config:
            single: Single
            _many: List[OneOfMany]

        expectedSpec = list(map(str.strip, """\
        [single]
        other = string
        [__many__]
        val = string\
        """.split('\n')))

        spec = core.to_spec(Config)
        self.assertEqual(expectedSpec, spec.write())

    def test_to_spec_4(self):

        @dataclass
        class OneOfMany:
            _name: str
            val: str

        @dataclass
        class Wrapper:
            _many: List[OneOfMany]

        @dataclass
        class Config:
            wrapper: Wrapper

        expectedSpec = list(map(str.strip, """\
        [wrapper]
        [[__many__]]
        val = string\
        """.split('\n')))

        spec = core.to_spec(Config)
        self.assertEqual(expectedSpec, spec.write())

    def test_type(self):
        T = TypeVar('T')

        def doit(klass: Type[T]) -> T:
            vars = {'other': 'test'}
            return klass(**vars)

        @dataclass
        class Parent:
            other: str

        self.assertEqual(doit(Parent).other, 'test')

    def test_lift_1(self):

        @dataclass
        class Single:
            other: str

        @dataclass
        class OneOfMany:
            _name: str
            val: str

        @dataclass
        class Config:
            single: Single
            _many: List[OneOfMany]

        infile = list(map(str.strip, """\
        [single]
        other = hello
        [one]
        val = apple
        [two]
        val = banana\
        """.split('\n')))

        expectedConfig = Config(
            single=Single(other = 'hello'),
            _many=[
                OneOfMany(_name = 'one', val = 'apple'),
                OneOfMany(_name = 'two', val = 'banana')
            ]
        )

        spec = core.to_spec(Config)
        root = configobj.ConfigObj(infile=infile, configspec=spec)
        config = core.lift(Config, root)
        self.assertEqual(expectedConfig, config)

    def test_lift_2(self):

        @dataclass
        class OneOfMany:
            _name: str
            val: str

        @dataclass
        class Wrapper:
            _many: List[OneOfMany]

        @dataclass
        class Config:
            wrapper: Wrapper

        infile = list(map(str.strip, """\
        [wrapper]
        [[one]]
        val = apple
        [[two]]
        val = banana\
        """.split('\n')))

        expectedConfig = Config(
            wrapper=Wrapper(
            _many=[
                OneOfMany(_name = 'one', val = 'apple'),
                OneOfMany(_name = 'two', val = 'banana')
            ]
            )
        )

        spec = core.to_spec(Config)
        root = configobj.ConfigObj(infile=infile, configspec=spec)
        config = core.lift(Config, root)
        self.assertEqual(expectedConfig, config)


    def test_lift_3(self):

        @dataclass
        class Foo:
            bar: str
            pip: int

        @dataclass
        class OneOfMany:
            _name: str
            val: str

        @dataclass
        class Wrapper:
            test: str
            foo: Foo
            _many: List[OneOfMany]

        @dataclass
        class Config:
            wrapper: Wrapper

        infile = list(map(str.strip, """\
        [wrapper]
        test = yes
        [[foo]]
        bar = testing
        pip = 123
        [[one]]
        val = apple
        [[two]]
        val = banana\
        """.split('\n')))

        expectedConfig = Config(
            wrapper=Wrapper(
            test='yes',
            foo=Foo('testing', 123),
            _many=[
                OneOfMany(_name = 'one', val = 'apple'),
                OneOfMany(_name = 'two', val = 'banana')
            ]
            )
        )


        spec = core.to_spec(Config)
        root = configobj.ConfigObj(infile=infile, configspec=spec)
        vtor = validate.Validator()
        root.validate(vtor)

        config = core.lift(Config, root)
        self.assertEqual(expectedConfig, config)

    def test_optional_root(self):
        @dataclass
        class Config:
            required: str
            optional: Optional[str] = None

        expectedSpec = list(map(str.strip, """\
        required = string
        optional = string(default=None)\
        """.split('\n')))

        spec = core.to_spec(Config)
        self.assertEqual(expectedSpec, spec.write())

        here = configobj.ConfigObj(infile= ["required = yes", "optional = here"], configspec=spec)
        vtor = validate.Validator()
        here.validate(vtor)
        self.assertEqual(Config('yes', 'here'), core.lift(Config, here))

        empty = configobj.ConfigObj(infile= ["required = yes"], configspec=spec)
        vtor = validate.Validator()
        empty.validate(vtor)
        self.assertEqual(Config('yes', None), core.lift(Config, empty))


    def test_readme_example(self):
        @dataclass
        class Single:
            other: str

        @dataclass
        class OneOfMany:
            _name: str
            val: str

        @dataclass
        class Config:
            single: Single
            _many: List[OneOfMany]
            optional: Optional[str] = None


        infile = list(map(str.strip, """\
        [single]
        other = hello
        [one]
        val = apple
        [two]
        val = banana\
        """.split('\n')))

        spec = core.to_spec(Config)
        root = configobj.ConfigObj(infile=infile, configspec=spec)

        validator = validate.Validator()
        root.validate(validator)
        
        expectedConfig = Config(
            single=Single(other='hello'),
            optional=None,
            _many=[
                OneOfMany(_name='one', val='apple'),
                OneOfMany(_name='two', val='banana')
            ]
        )

        config: Config = core.lift(Config, root)
        self.assertEqual(expectedConfig, config)
