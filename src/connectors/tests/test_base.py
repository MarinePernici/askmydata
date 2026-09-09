import unittest

from connectors.base import Connector


class IncompleteConnector(Connector):
    pass


class ConnectorTests(unittest.TestCase):
    def test_connector_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            Connector()

    def test_incomplete_connector_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            IncompleteConnector()