#!/usr/bin/env python3

import argparse
import json
import unittest

from otii_tester_client import OtiiTesterClient

JSON_FILE = None


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
                    timestamps_begin, timestamps_end, durations, consumptions = ret_val

                    # consumption metrics
                    min_consumed = min(consumptions)
                    max_consumed = max(consumptions)
                    avg_consumed = sum(consumptions) / len(consumptions)
                    count_consumed = len(consumptions)

                    # duration metrics
                    min_time = min(durations)
                    max_time = max(durations)
                    avg_time = sum(durations) / len(durations)

                    print("Timestamps of begin messages: {}".format(timestamps_begin))
                    print("Timestamps of end messages: {}".format(timestamps_end))
                    print("Durations: {}".format(durations))
                    print("Consumptions: {}".format(consumptions))

                    print("MIN CONSUMED = {} μWh".format(min_consumed * 10**6))
                    print("MAX CONSUMED = {} μWh".format(max_consumed * 10**6))
                    print("AVG CONSUMED = {} μWh".format(avg_consumed * 10**6))
                    print("COUNT = {}".format(count_consumed))

                    print("MIN TIME = {} ms".format(min_time))
                    print("MAX TIME = {} ms".format(max_time))
                    print("AVG TIME = {} ms".format(avg_time))

                    # if timeout = 0, the limit is infinite
                    if message_pair["timeout"] != 0:
                        self.assertLess(max_time, message_pair["timeout"], "Max interval duration is to long")
                    self.assertLess(avg_consumed, message_pair["avg_limit_high"] * 10**-6, "On average, this consumes to much energy")
                    self.assertGreater(avg_consumed, message_pair["avg_limit_low"] * 10**-6, "On average, this consumes to little energy")

                    # print afer assert that all is good
                    print("CONSUMPTION OK! (within specified limits)")

                else:
                    print("ERROR IN DATA! (check bellow)")
                    self.fail("Something went wrong in the recording -> Are there enough timestamps?")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Otii energy consumption analizer')
    parser.add_argument('-f', '--file', required=True, help='Json file with testing instructions')
    args, unknown = parser.parse_known_args()

    JSON_FILE = args.file

    # run tests
    arg_list = ['first-arg-is-ignored']
    arg_list.extend(unknown)
    unittest.main(argv=arg_list)
