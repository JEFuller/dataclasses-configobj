import unittest

from configobj import ConfigObj

from dataclasses_configobj import core

class CoreTestCase(unittest.TestCase):
    def test_to_spec(self):
        co = core.to_spec()
        self.assertIsInstance(co, ConfigObj)
