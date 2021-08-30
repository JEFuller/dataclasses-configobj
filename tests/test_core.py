from typing import List
import unittest
from dataclasses import dataclass

import configobj
from dataclasses_configobj import core


class CoreTestCase(unittest.TestCase):
    def test_to_spec_1(self):

        @dataclass
        class Foo:
            bar: str
            pip: int

        expectedSpec = list(map(str.strip, """\
        [Foo]
        bar = string
        pip = integer\
        """.split('\n')))

        root = configobj.ConfigObj()
        foo = configobj.Section(root, 1, root)
        root['Foo'] = foo
        foo.__setitem__('bar', 'string')
        foo.__setitem__('pip', 'integer')
        self.assertEqual(expectedSpec, root.write())

        spec = core.to_spec(Foo)
        self.assertEqual(expectedSpec, spec.write())

    def test_to_spec_2(self):

        @dataclass
        class Foo:
            a: str

        @dataclass
        class Bar:
            b: int

        expectedSpec = list(map(str.strip, """\
        [Foo]
        a = string
        [Bar]
        b = integer\
        """.split('\n')))

        root = configobj.ConfigObj()
        foo = configobj.Section(root, 1, root)
        root['Foo'] = foo
        foo.__setitem__('a', 'string')
        bar = configobj.Section(root, 1, root)
        root['Bar'] = bar
        bar.__setitem__('b', 'integer')
        self.assertEqual(expectedSpec, root.write())

        spec = core.to_spec([Foo, Bar])
        self.assertEqual(expectedSpec, spec.write())

    def test_to_spec_3(self):

        @dataclass
        class Parent:
            other: str

        @dataclass
        class Child:
            _name: str
            val: str

        expectedSpec = list(map(str.strip, """\
        [Parent]
        other = string
        [__many__]
        val = string\
        """.split('\n')))

        spec = core.to_spec([Parent, List[Child]])
        self.assertEqual(expectedSpec, spec.write())

    def test_lift(self):

        @dataclass
        class Parent:
            other: str

        @dataclass
        class Child:
            _name: str
            val: str

        infile = list(map(str.strip, """\
        [Parent]
        other = hello
        [one]
        val = apple
        [two]
        val = banana\
        """.split('\n')))

        expectedConfig = [Parent('hello'), Child('one', 'apple'), Child('two', 'banana')]

        spec = core.to_spec([Parent, List[Child]])

        root = configobj.ConfigObj(infile=infile, configspec=spec)
        config = core.lift([Parent, List[Child]], root)
        self.assertEqual(expectedConfig, config)
