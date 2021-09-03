from typing import Callable, Dict, List, Type, TypeVar
import unittest
from dataclasses import dataclass

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
            foo: Foo
            bar: Bar

        expectedSpec = list(map(str.strip, """\
        [foo]
        a = string
        [bar]
        b = integer\
        """.split('\n')))

        root = configobj.ConfigObj()
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
