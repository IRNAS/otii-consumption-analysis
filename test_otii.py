#!/usr/bin/env python3

import argparse
import json
import unittest

from otii_tester_client import OtiiTesterClient

JSON_FILE = "example.json"

# TODO: ali v json file pišemo porabo v Wh ali v μWh ???


def parse_file(filename):
    data = {}
    with open(filename) as f:
        data = json.load(f)
    return data


class OtiiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # load data from json:
        cls.json_data = parse_file(JSON_FILE)

        cls.otii_tester = OtiiTesterClient(cls.json_data["hostname"], cls.json_data["port"], cls.json_data["arc_name"])

    @classmethod
    def tearDownClass(cls):
        cls.otii_tester.close()

    def test_energy_consumption(self):
        # record data
        self.otii_tester.record_data(duration=self.json_data["record_duration"])

        # one subtest for each message pair
        for message_pair in self.json_data["message_pairs"]:
            with self.subTest(message_pair=message_pair):
                print("---------------------------------")
                print("FROM \"{}\" TO \"{}\"".format(message_pair["from"], message_pair["to"]))
                # analyze the result (msges):
                ret_val = self.otii_tester.get_energy_consumed_rx(message_pair["from"], message_pair["to"])  # for example
                if ret_val is not None:
                    min_consumed, max_consumed, avg_consumed, count_consumed = ret_val
                    print("MIN CONSUMED = {} μWh".format(min_consumed * 10**6))
                    print("MAX CONSUMED = {} μWh".format(max_consumed * 10**6))
                    print("AVG CONSUMED = {} μWh".format(avg_consumed * 10**6))
                    print("COUNT = {}".format(count_consumed))

                    self.assertLess(avg_consumed, message_pair["avg_limit_high"] * 10**-6, "One interval consumes to much energy")
                    self.assertGreater(avg_consumed, message_pair["avg_limit_low"] * 10**-6, "One interval consumes to little energy, is everything up and running?")

                    # print afer assert that all is good
                    print("CONSUMPTION OK! (within limits)")

                else:
                    print("CONSUMPTION NOT OK! (check bellow)")
                    self.fail("Something went wrong in the recording -> Are there enough timestamps?")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Otii energy consumtopn tester')
    parser.add_argument('-f', '--file', required=True, help='Json file with testing instructions')
    args = parser.parse_args()

    JSON_FILE = args.file

    # run tests
    suite = unittest.TestSuite()
    suite.addTest(OtiiTest('test_energy_consumption'))
    unittest.TextTestRunner(verbosity=2).run(suite)
