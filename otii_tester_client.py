import sys
import time
import subprocess
from otii_tcp_client import otii_connection, otii as otii_application


class OtiiTesterClient(object):

    def __init__(self, hostname, port, arc_name):
        self.hostname = hostname
        self.port = port
        self.arc_name = arc_name

        # initilization
        self.otii = self._connect_to_otii()
        self.arc = self._get_otii_arc()
        self._set_up_arc()  # with default values

    def _connect_to_otii(self):
        connection = otii_connection.OtiiConnection(self.hostname, self.port)
        connect_response = connection.connect_to_server()
        if connect_response["type"] == "error":
            print("Exit! Error code: " + connect_response["errorcode"] + ", Description: " + connect_response["payload"]["message"])
            sys.exit()
        otii = otii_application.Otii(connection)

        return otii

    def _get_otii_arc(self):
        devices = self.otii.get_devices()
        #print("Device name: {}".format(devices[0].name))
        if len(devices) == 0:
            print("No Arc connected!")
            sys.exit()
        devices = [device for device in devices if device.name == self.arc_name]
        if len(devices) != 1:
            print("Expected to find exactly 1 device named {0}, found {1} devices".format(self.arc_name, len(devices)))
            sys.exit()
        arc = devices[0]

        return arc

    def _set_up_arc(self, main_voltage=3.3, exp_voltage=3.3, max_current=0.5, uart_baudrate=115200, enable_uar=True, enable_exp=True, enable_5v=True):
        self.arc.set_main_voltage(3.3)
        self.arc.set_exp_voltage(3.3)
        self.arc.set_max_current(0.5)
        self.arc.set_uart_baudrate(115200)
        self.arc.enable_uart(True)
        self.arc.enable_exp_port(True)
        self.arc.enable_5v(True)  # The switch board is powerd by the Otii +5V pin

    def close(self):
        self.arc.enable_5v(False)
        self.arc.set_main(False)

    def upload_firmware(self, command):
        '''Enable upload on Arc and execure shell command for uploading'''
        # TODO: will this be used?
        self.arc.enable_5v(True)  # The switch board is powered by the Otii +5V pin.

        # Turn on the main power, and give the device time to startup.
        self.arc.set_main(True)
        time.sleep(1.0)

        # Enable the USB, and give the ST-lINK time to startup
        self.arc.set_gpo(1, True)
        time.sleep(3.0)

        # Upload new firmware
        result = subprocess.call(command, shell=False, stderr=subprocess.DEVNULL)
        if result != 0:
            print("Failed to upload new firmware")
            sys.exit()
        time.sleep(3.0)

        # Disable the USB, and turn off the main power
        self.arc.set_gpo(1, False)
        time.sleep(1.0)
        self.arc.set_main_voltage(0.5)
        time.sleep(1.0)
        self.arc.set_main(False)
        self.arc.set_main_voltage(3.3)
        time.sleep(2.0)

    def record_data(self, duration=5):
        '''Records data for specified duration (blocking)'''
        # fetch project data
        self.project = self.otii.get_active_project()
        if not self.project:
            self.project = self.otii.create_project()

        # turn everything on
        self.arc.enable_5v(True)
        self.arc.set_gpo(1, False) #disconnect programmer
        self.arc.set_gpo(2, True)

        self.arc.enable_channel("mc", True)
        self.arc.enable_channel("me", True)
        self.arc.enable_channel("i1", True)
        self.arc.enable_channel("rx", True)

        # record the data        
        self.project.start_recording()
        time.sleep(1.0)
        self.arc.set_main(True)
        time.sleep(duration)
        self.project.stop_recording()

        # turn back off
        self.arc.set_main(False)
        self.arc.set_gpo(1, False)
        self.arc.set_gpo(2, False)
        self.arc.enable_5v(False)

    def recording_start(self):
        '''Start data recording'''
        self.project = self.otii.get_active_project()
        if not self.project:
            self.project = self.otii.create_project()

        # turn everything on
        self.arc.enable_5v(True)
        self.arc.set_gpo(1, True)
        self.arc.set_gpo(2, True)

        self.arc.enable_channel("mc", True)
        self.arc.enable_channel("me", True)
        self.arc.enable_channel("i1", True)
        self.arc.enable_channel("rx", True)

        # record the data
        self.arc.set_main(True)
        self.project.start_recording()

    def recording_stop(self):
        '''Stop data recording'''
        self.project.stop_recording()

        # turn everything off
        self.arc.set_main(False)
        self.arc.set_gpo(1, False)
        self.arc.set_gpo(2, False)
        self.arc.enable_5v(False)

    def get_message_timestamps(self, msg):
        '''Check if the specified message is present in the recording'''
        recording = self.project.get_last_recording()
        index = 0
        count = recording.get_channel_data_count(self.arc.id, "rx")
        data = recording.get_channel_data(self.arc.id, "rx", index, count)
        values = data["values"]
        timestamps = [value["timestamp"] for value in values if msg in value["value"]]
        return timestamps

    def get_energy_consumed_rx(self, msg_begin, msg_end):
        '''Calculate energy consumption between two messages sent'''
        recording = self.project.get_last_recording()
        index = 0
        count = recording.get_channel_data_count(self.arc.id, "rx")
        data = recording.get_channel_data(self.arc.id, "rx", index, count)
        values = data["values"]
        timestamps_begin = [value["timestamp"] for value in values if msg_begin in value["value"]]
        timestamps_end = [value["timestamp"] for value in values if msg_end in value["value"]]

        # if the messages are the same, adjust timestamp arrays
        if msg_begin == msg_end:
            timestamps_begin = timestamps_begin[0:-1]  # skip last
            timestamps_end = timestamps_end[1:]  # skip first

        # first begin msg might have bigger timestamp then the first end msg (we dont know where in the loop we start listening)
        # if this is the case, remove the first element from the second list:
        if timestamps_begin[0] > timestamps_end[0]:
            timestamps_end = timestamps_end[1:]

        if len(timestamps_begin) == 0 or len(timestamps_end) == 0:
            return None

        durations = []
        consumptions = []

        for tsb, tse in zip(timestamps_begin, timestamps_end):
            start = recording.get_channel_data_index(self.arc.id, "me", tsb)
            if start > 0:
                start = start - 1
            stop = recording.get_channel_data_index(self.arc.id, "me", tse)
            count = stop - start
            data = recording.get_channel_data(self.arc.id, "me", start, 1)
            start_energy = data["values"][0]
            data = recording.get_channel_data(self.arc.id, "me", stop - 1, 1)
            stop_energy = data["values"][0]
            consumed = (stop_energy - start_energy) / 3600

            consumptions.append(consumed)

            # if consumed > max_consumed:
            #     max_consumed = consumed
            # if consumed < min_consumed:
            #     min_consumed = consumed
            # count_consumed += 1
            # avg_consumed += consumed

            # duration of this consumption
            durations.append(abs(tsb - tse))

        return (timestamps_begin, timestamps_end, durations, consumptions)

    def get_energy_consumed_gpi1(self):
        '''Calculate energy consumption between two small pulses over GPI1'''
        # TODO: test this - do we even use gpi1 pulses in any project?
        recording = self.project.get_last_recording()
        index = 0
        count = recording.get_channel_data_count(self.arc.id, "i1")
        gpi1_data = recording.get_channel_data(self.arc.id, "i1", index, count)["values"]
        timestamps = [gpi1_value["timestamp"] for gpi1_value in gpi1_data]
        if len(timestamps) < 4:  # Need at least two GPI1 pulses
            return None

        timestamps_begin = timestamps[0::2]
        timestamps_end = timestamps[2::2]

        durations = []
        consumptions = []

        for tsb, tse in zip(timestamps_begin, timestamps_end):
            start = recording.get_channel_data_index(self.arc.id, "me", tsb)
            if start > 0:
                start = start - 1
            stop = recording.get_channel_data_index(self.arc.id, "me", tse)
            count = stop - start
            data = recording.get_channel_data(self.arc.id, "me", start, 1)
            start_energy = data["values"][0]
            data = recording.get_channel_data(self.arc.id, "me", stop - 1, 1)
            stop_energy = data["values"][0]
            consumed = (stop_energy - start_energy) / 3600

            consumptions.append(consumed)
            durations.append(tsb - tse)

        return (timestamps_begin, timestamps_end, durations, consumptions)
