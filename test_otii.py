#!/usr/bin/env python3
import unittest
from otii_tester import OtiiTesterClient

HOSTNAME = '127.0.0.1'  # Whre is the otii connected?
PORT = 1905
ARC_NAME = "TestArc1"   # Configure each otii with an unique name


class OtiiTest(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.otii_tester = OtiiTesterClient(HOSTNAME, PORT, ARC_NAME)

    def test_energy_consumption(self):
        # record data
        self.otii_tester.record_data(duration=10)  # record for 10 seconds

        # analyze the result:
        consumed = self.otii_tester.get_energy_consumed_rx("fsm(1, 1, 1)", "fsm(2, 3, 8)")  # for example

        self.assertLess(consumed, 0.0004, "One interval consumes to much energy")
        self.assertGreater(consumed, 0.0002, "One interval consumes to little energy, is everything up and running?")
        # TODO: add yaml read and test them all


if __name__ == '__main__':
    unittest.main()
